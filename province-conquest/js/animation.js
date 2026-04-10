// ========================================
// 省份争霸 - 动画控制核心模块
// 负责协调数据、对决、地图渲染，驱动整个自动播放动画
// ========================================

// ========================================
// 工具函数
// ========================================

/**
 * 延迟函数 - 返回Promise，用于控制动画节奏
 * @param {number} ms - 延迟毫秒数
 * @returns {Promise<void>}
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ========================================
// 右侧PK区域展示
// ========================================

/**
 * 更新所有对决的列表（含6维度对比详情）
 * @param {Array} battles - 对决数组
 */
function updateBattlesList(battles) {
  const battlesList = document.getElementById('battlesList');
  if (!battlesList) return;

  battlesList.innerHTML = battles.map(duel => {
    const attackerColor = provinceData[duel.attacker.key]?.color || '#666';
    const defenderColor = provinceData[duel.defender.key]?.color || '#666';
    const winnerName = duel.winner === 'attacker' ? duel.attacker.name : duel.defender.name;

    // 生成6维度对比条
    const dimensionRows = (duel.dimensions || []).map(dim => {
      const total = dim.attackerValue + dim.defenderValue;
      const leftPct = total > 0 ? (dim.attackerValue / total * 100).toFixed(1) : 50;
      const rightPct = total > 0 ? (dim.defenderValue / total * 100).toFixed(1) : 50;
      const leftWin = dim.winner === 'attacker' ? ' win' : '';
      const rightWin = dim.winner === 'defender' ? ' win' : '';
      return `
        <div class="dim-row">
          <span class="dim-val left${leftWin}">${dim.attackerValue}</span>
          <div class="dim-bar-wrap">
            <div class="dim-fill left" style="width:${leftPct}%;background:${attackerColor}"></div>
            <span class="dim-label">${dim.name}</span>
            <div class="dim-fill right" style="width:${rightPct}%;background:${defenderColor}"></div>
          </div>
          <span class="dim-val right${rightWin}">${dim.defenderValue}</span>
        </div>`;
    }).join('');

    return `
      <div class="battle-item">
        <div class="battle-header">
          <span class="attacker-name" style="color:${attackerColor}">${duel.attacker.name}</span>
          <span class="vs-badge">VS</span>
          <span class="defender-name" style="color:${defenderColor}">${duel.defender.name}</span>
        </div>
        <div class="dimension-rows">${dimensionRows}</div>
        <div class="battle-score">
          <span class="score-text">${duel.score.attacker} : ${duel.score.defender}</span>
          <span class="winner-badge">${winnerName} 胜</span>
        </div>
      </div>
    `;
  }).join('');
}

// 属性标签缩写与颜色
const statTagConfig = {
  command:  { abbr: '统', color: '#e74c3c' },
  martial:  { abbr: '武', color: '#e67e22' },
  wisdom:   { abbr: '智', color: '#3498db' },
  politics: { abbr: '政', color: '#2ecc71' },
  charisma: { abbr: '魅', color: '#9b59b6' },
  craft:    { abbr: '技', color: '#f1c40f' }
};

/**
 * 更新名人列表（按省份分组，展示名人卡片）
 * @param {Object} gameState - 游戏状态
 */
function updateHeroesList(gameState) {
  const heroesList = document.getElementById('heroesList');
  if (!heroesList) return;

  // 按省份分组
  const groups = [];
  for (const key in gameState.provinces) {
    const province = gameState.provinces[key];
    if (province.conquered) continue;
    const heroes = getEffectiveHeroes(key, gameState);
    if (heroes.length === 0) continue;
    groups.push({
      name: province.name,
      color: provinceData[key]?.color || '#666',
      heroes: heroes
    });
  }

  heroesList.innerHTML = groups.map(g => {
    const heroCards = g.heroes.map(hero => {
      const statTags = dimensionKeys.map(k => {
        const cfg = statTagConfig[k];
        return `<span class="stat-tag" style="border-color:${cfg.color};color:${cfg.color}">${cfg.abbr}${hero.stats[k]}</span>`;
      }).join('');
      return `
        <div class="hero-card">
          <div class="hero-name">${hero.name}</div>
          <div class="hero-title">${hero.title}</div>
          <div class="hero-stats-mini">${statTags}</div>
        </div>`;
    }).join('');

    return `
      <div class="province-heroes-group">
        <div class="province-group-header">
          <span class="province-dot" style="background:${g.color}"></span>
          <span class="province-group-name">${g.name}</span>
          <span class="hero-count">${g.heroes.length}人</span>
        </div>
        <div class="hero-cards">${heroCards}</div>
      </div>`;
  }).join('');
}

/**
 * 添加历史对决记录
 * @param {Object} duelResult - 对决结果对象
 */
function addHistoryRecord(duelResult) {
  const historyList = document.getElementById('historyList');
  if (!historyList) return;

  const winnerName = duelResult.winner === 'attacker' ? duelResult.attacker.name : duelResult.defender.name;
  const loserName = duelResult.winner === 'attacker' ? duelResult.defender.name : duelResult.attacker.name;

  const recordDiv = document.createElement('div');
  recordDiv.className = 'history-item';
  recordDiv.innerHTML = `
    <span class="history-winner">${winnerName}</span>
    <span class="history-vs">→</span>
    <span class="history-loser">${loserName}</span>
  `;

  historyList.insertBefore(recordDiv, historyList.firstChild);

  // 最多保存30条历史记录
  while (historyList.children.length > 30) {
    historyList.removeChild(historyList.lastChild);
  }
}

// ========================================
// 高亮所有交战省份
// ========================================

/**
 * 高亮所有交战省份
 * @param {Array} battles - 对决数组
 * @param {Object} gameState - 游戏状态
 * @returns {Function} cleanup函数
 */
function highlightAllBattleProvinces(battles, gameState) {
  if (!chart) return () => {};

  const battlePairs = battles.map(d => ({
    attacker: d.attacker.key,
    defender: d.defender.key
  }));

  let flashState = true;

  const buildData = (isFlash) => {
    const result = [];
    for (const key in provinceData) {
      const p = provinceData[key];
      const state = gameState.provinces[key];
      let color = p.color;
      let borderColor = '#1a1a2e';
      let borderWidth = 1;

      // 如果已被征服，使用最终统治者的颜色
      if (state && state.conquered) {
        const rulerKey = getRuler(key, gameState);
        if (rulerKey && rulerKey !== key) {
          const rulerProvince = provinceData[rulerKey];
          if (rulerProvince) {
            color = rulerProvince.color;
          }
        }
      }

      // 检查是否是交战省份
      const isBattleProvince = battlePairs.some(pair =>
        key === pair.attacker || key === pair.defender
      );

      if (isBattleProvince) {
        if (isFlash) {
          borderColor = '#ffd700';
          borderWidth = 3;
        } else {
          borderColor = '#ffd700';
          borderWidth = 2;
        }
      }

      result.push({
        name: p.name,
        key: key,
        itemStyle: {
          areaColor: color,
          borderColor: borderColor,
          borderWidth: borderWidth
        },
        label: {
          show: true,
          formatter: params => params.name
        }
      });
    }
    return result;
  };

  // 初始设置
  chart.setOption({
    series: [{
      data: buildData(false)
    }]
  });

  // 闪烁动画
  const battleHighlightTimer = setInterval(() => {
    flashState = !flashState;
    chart.setOption({
      series: [{
        data: buildData(flashState)
      }]
    });
  }, 500);

  // 返回cleanup函数
  return function cleanup() {
    clearInterval(battleHighlightTimer);
  };
}

// ========================================
// 单轮动画（并发执行）
// ========================================

/**
 * 播放单轮动画（并发执行所有对决）
 * @param {Object} gameState - 游戏状态
 * @returns {Promise<Object>} 更新后的游戏状态
 */
async function playRound(gameState) {
  // 1. 执行一轮对决
  const roundResult = executeRound(gameState);
  const { gameState: newGameState, battles } = roundResult;

  // 保存当前游戏状态到全局，供其他函数使用
  window.currentGameState = newGameState;

  if (battles.length === 0) {
    await delay(500);
    return newGameState;
  }

  // 2. 同时展示所有对决
  updateBattlesList(battles);
  updateHeroesList(newGameState);

  // 3. 高亮所有交战省份（使用旧状态）
  const cleanup = highlightAllBattleProvinces(battles, gameState);

  // 4. 等待观众看清
  await delay(2000);

  // 5. 同时播放所有征服动画
  const conquestPromises = battles.map(duel => {
    const winnerKey = duel.winner === 'attacker' ? duel.attacker.key : duel.defender.key;
    const loserKey = duel.winner === 'attacker' ? duel.defender.key : duel.attacker.key;
    // 使用旧状态，确保失败省份显示原色
    return animateConquest(winnerKey, loserKey, gameState, provinceData[loserKey].color);
  });

  await Promise.all(conquestPromises);

  // 6. 添加所有历史记录
  battles.forEach(duel => addHistoryRecord(duel));

  // 7. 取消高亮
  cleanup();

  // 8. 更新地图颜色
  updateMapColors(newGameState);

  // 9. 轮间停顿
  await delay(800);

  return newGameState;
}

// ========================================
// 胜利动画
// ========================================

/**
 * 播放胜利动画
 * @param {string} championKey - 冠军省份key
 * @param {Object} gameState - 游戏状态
 */
async function playVictoryAnimation(championKey, gameState) {
  // 1. 等待1秒
  await delay(1000);

  const overlay = document.getElementById('victoryOverlay');
  const provinceEl = document.getElementById('victoryProvince');
  const heroesListEl = document.getElementById('victoryHeroesList');

  if (!overlay) return;

  // 2. 显示胜利浮层
  overlay.classList.add('active');

  // 3. 设置冠军省份名称
  const championProvince = provinceData[championKey];
  if (provinceEl && championProvince) {
    provinceEl.textContent = championProvince.name;
  }

  // 4. 渲染雷达图
  renderVictoryRadar(championKey, gameState);

  // 5. 生成名人列表
  if (heroesListEl) {
    const heroes = getEffectiveHeroes(championKey, gameState);
    heroesListEl.innerHTML = heroes.map((hero, index) => `
      <div class="hero-tag" style="animation-delay: ${index * 0.1}s">
        ${hero.name} · ${hero.title}
      </div>
    `).join('');
  }
}

// ========================================
// 自动播放主循环
// ========================================

/**
 * 自动播放主循环
 */
async function startAnimation() {
  try {
    // 1. 初始化地图
    await initMap();

    // 2. 初始化游戏状态
    let gameState = initGameState();
    window.currentGameState = gameState;

    // 3. 更新初始地图颜色
    updateMapColors(gameState);

    // 4. 初始化名人列表
    updateHeroesList(gameState);

    // 5. 显示开场动画（标题淡入，等待2秒）
    await delay(2000);

    // 6. 进入主循环
    while (true) {
      const aliveCount = getAliveProvinces(gameState).length;

      if (aliveCount <= 1) {
        break;
      }

      gameState = await playRound(gameState);
    }

    // 7. 播放胜利动画
    const finalAlive = getAliveProvinces(gameState);
    if (finalAlive.length === 1) {
      await playVictoryAnimation(finalAlive[0], gameState);
    }
  } catch (error) {
    console.error('动画播放出错:', error);
  }
}

// ========================================
// 页面加载自动启动
// ========================================

window.addEventListener('DOMContentLoaded', () => {
  startAnimation();
});
