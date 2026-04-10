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
 * 更新所有对决的列表
 * @param {Array} battles - 对决数组
 */
function updateBattlesList(battles) {
  const battlesList = document.getElementById('battlesList');
  if (!battlesList) return;

  battlesList.innerHTML = battles.map(duel => {
    const winnerName = duel.winner === 'attacker' ? duel.attacker.name : duel.defender.name;

    return `
      <div class="battle-item">
        <div class="battle-provinces">
          <div class="battle-province">
            <div class="province-dot" style="background-color: ${provinceData[duel.attacker.key]?.color || '#666'}"></div>
            <span class="province-name-small">${duel.attacker.name}</span>
          </div>
          <span class="battle-vs">VS</span>
          <div class="battle-province right">
            <span class="province-name-small">${duel.defender.name}</span>
            <div class="province-dot" style="background-color: ${provinceData[duel.defender.key]?.color || '#666'}"></div>
          </div>
        </div>
        <div class="battle-result-small winner">
          ${winnerName} 获胜
        </div>
      </div>
    `;
  }).join('');
}

/**
 * 更新名人列表
 * @param {Object} gameState - 游戏状态
 */
function updateHeroesList(gameState) {
  const heroesList = document.getElementById('heroesList');
  if (!heroesList) return;

  const allHeroes = [];
  for (const key in gameState.provinces) {
    const province = gameState.provinces[key];
    const heroes = getEffectiveHeroes(key, gameState);
    allHeroes.push(...heroes.map(h => ({
      ...h,
      province: province.name
    })));
  }

  heroesList.innerHTML = allHeroes.map(hero => `
    <div class="hero-chip">
      ${hero.name}
    </div>
  `).join('');
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

      // 如果已被征服，使用征服者的颜色
      if (state && state.conquered && state.conqueredBy && state.conqueredBy !== key) {
        const ownerProvince = provinceData[state.conqueredBy];
        if (ownerProvince) {
          color = ownerProvince.color;
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
