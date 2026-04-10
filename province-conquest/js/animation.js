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
// 状态栏更新
// ========================================

/**
 * 更新底部状态栏
 * @param {number} round - 当前轮次
 * @param {number} aliveCount - 存活省份数量
 */
function updateStatusBar(round, aliveCount) {
  const roundElement = document.getElementById('roundNumber');
  const aliveElement = document.getElementById('aliveCount');
  
  if (roundElement) {
    roundElement.textContent = round;
  }
  if (aliveElement) {
    aliveElement.textContent = aliveCount;
  }
}

// ========================================
// 对决浮层展示
// ========================================

/**
 * 显示对决浮层
 * @param {Object} duelResult - 对决结果对象
 */
function showBattleOverlay(duelResult) {
  const overlay = document.getElementById('battleOverlay');
  if (!overlay) return;

  // 更新省份名称
  const attackerNameEl = document.getElementById('attackerName');
  const defenderNameEl = document.getElementById('defenderName');
  
  if (attackerNameEl) attackerNameEl.textContent = duelResult.attacker.name;
  if (defenderNameEl) defenderNameEl.textContent = duelResult.defender.name;

  // 更新名人信息（显示第一个名人作为代表）
  const attackerHeroEl = document.getElementById('attackerHero');
  const defenderHeroEl = document.getElementById('defenderHero');
  
  const attackerHeroes = getEffectiveHeroes(duelResult.attacker.key, { provinces: window.currentGameState?.provinces || {} });
  const defenderHeroes = getEffectiveHeroes(duelResult.defender.key, { provinces: window.currentGameState?.provinces || {} });
  
  if (attackerHeroEl) {
    const firstHero = attackerHeroes[0];
    attackerHeroEl.textContent = firstHero ? `${firstHero.name} · ${firstHero.title}` : '-';
  }
  if (defenderHeroEl) {
    const firstHero = defenderHeroes[0];
    defenderHeroEl.textContent = firstHero ? `${firstHero.name} · ${firstHero.title}` : '-';
  }

  // 生成6维度对比条形
  const dimensionsContainer = document.getElementById('battleDimensions');
  if (dimensionsContainer) {
    dimensionsContainer.innerHTML = generateDimensionBars(duelResult);
  }

  // 更新结果文本
  const resultEl = document.getElementById('battleResult');
  if (resultEl) {
    const winnerName = duelResult.winner === 'attacker' ? duelResult.attacker.name : duelResult.defender.name;
    resultEl.textContent = `${winnerName} 获胜！`;
    resultEl.className = 'battle-result show victory';
  }

  // 显示浮层
  overlay.classList.add('active');
  overlay.classList.remove('fade-out');
}

/**
 * 生成维度对比条形的HTML
 * @param {Object} duelResult - 对决结果
 * @returns {string} HTML字符串
 */
function generateDimensionBars(duelResult) {
  const { dimensions, attacker, defender, winner } = duelResult;
  
  return dimensions.map(dim => {
    const total = dim.attackerValue + dim.defenderValue;
    const attackerWidth = total > 0 ? (dim.attackerValue / total * 100) : 50;
    const defenderWidth = total > 0 ? (dim.defenderValue / total * 100) : 50;
    
    const attackerWin = dim.winner === 'attacker';
    const defenderWin = dim.winner === 'defender';
    
    return `
      <div class="dimension-row">
        <div class="dimension-label">${dim.name}</div>
        <div class="dimension-bars">
          <div class="bar-side left">
            <span class="bar-value">${dim.attackerValue}</span>
            <div class="bar-fill ${attackerWin ? 'winner' : ''}" style="width: ${attackerWidth}%"></div>
          </div>
          <div class="bar-side right">
            <div class="bar-fill ${defenderWin ? 'winner' : ''}" style="width: ${defenderWidth}%"></div>
            <span class="bar-value">${dim.defenderValue}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * 隐藏对决浮层
 */
function hideBattleOverlay() {
  const overlay = document.getElementById('battleOverlay');
  if (!overlay) return;

  overlay.classList.add('fade-out');
  overlay.classList.remove('active');
}

// ========================================
// 单轮动画
// ========================================

/**
 * 播放单轮动画
 * @param {Object} gameState - 游戏状态
 * @returns {Promise<Object>} 更新后的游戏状态
 */
async function playRound(gameState) {
  // 1. 更新底部状态栏
  updateStatusBar(gameState.round, getAliveProvinces(gameState).length);

  // 2. 执行一轮对决
  const roundResult = executeRound(gameState);
  const { gameState: newGameState, battles } = roundResult;

  // 保存当前游戏状态到全局，供其他函数使用
  window.currentGameState = newGameState;

  // 3. 对每场对决依次播放动画
  for (const duel of battles) {
    const attackerKey = duel.attacker.key;
    const defenderKey = duel.defender.key;
    const winnerKey = duel.winner === 'attacker' ? attackerKey : defenderKey;
    const loserKey = duel.winner === 'attacker' ? defenderKey : attackerKey;

    // a. 高亮交战双方省份
    const cleanup = highlightBattleProvinces(attackerKey, defenderKey, gameState);

    // b. 显示对决浮层
    showBattleOverlay(duel);

    // c. 等待1.5秒让观众看清
    await delay(1500);

    // d. 播放征服动画
    await animateConquest(winnerKey, loserKey, newGameState);

    // e. 隐藏对决浮层
    hideBattleOverlay();

    // f. 取消高亮
    cleanup();

    // g. 更新地图颜色
    updateMapColors(newGameState);

    // 对决间隔0.3秒
    await delay(300);
  }

  // 4. 轮间停顿0.5秒
  await delay(500);

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

    // 4. 显示开场动画（标题淡入，等待2秒）
    await delay(2000);

    // 5. 进入主循环
    while (true) {
      const aliveCount = getAliveProvinces(gameState).length;
      
      if (aliveCount <= 1) {
        break;
      }

      gameState = await playRound(gameState);
    }

    // 6. 播放胜利动画
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
