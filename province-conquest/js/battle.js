// ========================================
// 省份争霸 - 战斗系统核心模块
// ========================================

// 维度中文名映射
const dimensionNames = {
  command: "统帅",
  martial: "武力",
  wisdom: "智谋",
  politics: "政治",
  charisma: "魅力",
  craft: "技艺"
};

// 六维属性键列表
const dimensionKeys = ["command", "martial", "wisdom", "politics", "charisma", "craft"];

/**
 * 初始化游戏状态
 * @returns {Object} 初始游戏状态
 */
function initGameState() {
  const provinces = {};
  
  for (const [key, data] of Object.entries(provinceData)) {
    provinces[key] = {
      ...data,
      conquered: false,
      conqueredBy: null,
      absorbedHeroes: []
    };
  }
  
  return {
    provinces: provinces,
    round: 0,
    history: []
  };
}

/**
 * 获取所有存活（未被征服）的省份key列表
 * @param {Object} gameState - 游戏状态
 * @returns {string[]} 存活省份key数组
 */
function getAliveProvinces(gameState) {
  return Object.keys(gameState.provinces).filter(key => {
    const province = gameState.provinces[key];
    return !province.conquered;
  });
}

/**
 * 获取省份的有效名人（原始 + 吸收的）
 * @param {string} provinceKey - 省份key
 * @param {Object} gameState - 游戏状态
 * @returns {Array} 名人列表
 */
function getEffectiveHeroes(provinceKey, gameState) {
  const province = gameState.provinces[provinceKey];
  if (!province) return [];
  
  // 如果该省份已被征服，返回空数组（名人已被转移到征服者）
  if (province.conquered) {
    return [];
  }
  
  // 原始名人 + 吸收的名人
  return [...(province.heroes || []), ...(province.absorbedHeroes || [])];
}

/**
 * 计算省份六维总和
 * @param {string} provinceKey - 省份key
 * @param {Object} gameState - 游戏状态
 * @returns {Object} 六维总和及总计
 */
function getProvinceStats(provinceKey, gameState) {
  const heroes = getEffectiveHeroes(provinceKey, gameState);
  
  const stats = {
    command: 0,
    martial: 0,
    wisdom: 0,
    politics: 0,
    charisma: 0,
    craft: 0,
    total: 0
  };
  
  for (const hero of heroes) {
    if (hero.stats) {
      for (const key of dimensionKeys) {
        stats[key] += hero.stats[key] || 0;
      }
    }
  }
  
  // 计算总和
  stats.total = dimensionKeys.reduce((sum, key) => sum + stats[key], 0);
  
  return stats;
}

/**
 * 查找省份的当前统治者
 * 如果省份已被征服，递归找到最终的征服者
 * @param {string} provinceKey - 省份key
 * @param {Object} gameState - 游戏状态
 * @returns {string|null} 统治者省份key，如果未被征服则返回自身
 */
function getRuler(provinceKey, gameState) {
  const province = gameState.provinces[provinceKey];
  if (!province) return null;
  
  if (!province.conquered) {
    return provinceKey;
  }
  
  // 递归查找征服者
  if (province.conqueredBy) {
    return getRuler(province.conqueredBy, gameState);
  }
  
  return null;
}

/**
 * 执行分维度对决
 * @param {string} attackerKey - 攻击方省份key
 * @param {string} defenderKey - 防守方省份key
 * @param {Object} gameState - 游戏状态
 * @returns {Object} 对决详情
 */
function executeDuel(attackerKey, defenderKey, gameState) {
  const attackerProvince = gameState.provinces[attackerKey];
  const defenderProvince = gameState.provinces[defenderKey];
  
  const attackerStats = getProvinceStats(attackerKey, gameState);
  const defenderStats = getProvinceStats(defenderKey, gameState);
  
  // 逐维比较
  const dimensions = [];
  let attackerScore = 0;
  let defenderScore = 0;
  
  for (const key of dimensionKeys) {
    const attackerValue = attackerStats[key];
    const defenderValue = defenderStats[key];
    
    let winner;
    if (attackerValue > defenderValue) {
      winner = "attacker";
      attackerScore++;
    } else if (defenderValue > attackerValue) {
      winner = "defender";
      defenderScore++;
    } else {
      // 平局时攻方胜（进攻优势）
      winner = "attacker";
      attackerScore++;
    }
    
    dimensions.push({
      name: dimensionNames[key],
      key: key,
      attackerValue: attackerValue,
      defenderValue: defenderValue,
      winner: winner
    });
  }
  
  // 判定胜负
  let winner;
  let isTie = false;
  
  if (attackerScore > defenderScore) {
    winner = "attacker";
  } else if (defenderScore > attackerScore) {
    winner = "defender";
  } else {
    // 3:3 平局处理
    isTie = true;
    if (attackerStats.total > defenderStats.total) {
      winner = "attacker";
    } else if (defenderStats.total > attackerStats.total) {
      winner = "defender";
    } else {
      // 总和也相同，攻方胜（进攻优势）
      winner = "attacker";
    }
  }
  
  return {
    attacker: {
      key: attackerKey,
      name: attackerProvince.name,
      stats: attackerStats
    },
    defender: {
      key: defenderKey,
      name: defenderProvince.name,
      stats: defenderStats
    },
    dimensions: dimensions,
    score: {
      attacker: attackerScore,
      defender: defenderScore
    },
    winner: winner,
    isTie: isTie
  };
}

/**
 * 合并省份（胜者吸收败者）
 * @param {string} winnerKey - 胜者省份key
 * @param {string} loserKey - 败者省份key
 * @param {Object} gameState - 游戏状态
 * @returns {Object} 更新后的游戏状态
 */
function mergeProvinces(winnerKey, loserKey, gameState) {
  // 创建新的游戏状态（避免直接修改原对象）
  const newGameState = JSON.parse(JSON.stringify(gameState));
  
  const winner = newGameState.provinces[winnerKey];
  const loser = newGameState.provinces[loserKey];
  
  if (!winner || !loser) {
    return newGameState;
  }
  
  // 获取败者的所有有效名人
  const loserHeroes = getEffectiveHeroes(loserKey, gameState);
  
  // 胜方吸收败方所有名人
  winner.absorbedHeroes = winner.absorbedHeroes || [];
  winner.absorbedHeroes.push(...loserHeroes);
  
  // 标记败方为已征服
  loser.conquered = true;
  loser.conqueredBy = winnerKey;
  
  return newGameState;
}

/**
 * 随机打乱数组（Fisher-Yates算法）
 * @param {Array} array - 要打乱的数组
 * @returns {Array} 打乱后的新数组
 */
function shuffleArray(array) {
  const newArray = [...array];
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
}

/**
 * 获取省份的相邻存活统治者列表
 * @param {string} provinceKey - 省份key
 * @param {Object} gameState - 游戏状态
 * @returns {string[]} 相邻统治者key数组（排除自己）
 */
function getAdjacentRulers(provinceKey, gameState) {
  const province = gameState.provinces[provinceKey];
  if (!province || province.conquered) return [];
  
  const rulers = new Set();
  const adjList = province.adj || [];
  
  for (const adjKey of adjList) {
    const rulerKey = getRuler(adjKey, gameState);
    // 排除自己和已被征服的省份
    if (rulerKey && rulerKey !== provinceKey) {
      rulers.add(rulerKey);
    }
  }
  
  return Array.from(rulers);
}

/**
 * 执行一轮全局混战
 * @param {Object} gameState - 游戏状态
 * @returns {Object} 本轮结果和更新后的游戏状态
 */
function executeRound(gameState) {
  // 创建新的游戏状态
  let currentState = JSON.parse(JSON.stringify(gameState));
  
  // 1. 获取所有存活省份
  const aliveProvinces = getAliveProvinces(currentState);
  
  // 如果没有存活省份或只剩一个，结束游戏
  if (aliveProvinces.length <= 1) {
    return {
      gameState: currentState,
      battles: [],
      round: currentState.round,
      aliveCount: aliveProvinces.length
    };
  }
  
  // 2. 随机打乱顺序
  const shuffledProvinces = shuffleArray(aliveProvinces);
  
  // 3. 生成配对
  const battles = [];
  const paired = new Set(); // 记录已配对的省份
  const duelResults = [];
  
  for (const provinceKey of shuffledProvinces) {
    // 如果该省份已经被配对过，跳过
    if (paired.has(provinceKey)) continue;
    
    // 获取相邻的存活统治者
    const adjacentRulers = getAdjacentRulers(provinceKey, currentState);
    
    // 过滤掉已经配对的对手
    const availableOpponents = adjacentRulers.filter(ruler => !paired.has(ruler));
    
    if (availableOpponents.length === 0) {
      // 没有可用对手，尝试找任何其他存活省份
      const otherProvinces = aliveProvinces.filter(
        key => key !== provinceKey && !paired.has(key)
      );
      
      if (otherProvinces.length === 0) {
        continue; // 没有对手，跳过
      }
      
      // 随机选择一个对手
      const randomOpponent = otherProvinces[Math.floor(Math.random() * otherProvinces.length)];
      
      // 4. 配对去重
      paired.add(provinceKey);
      paired.add(randomOpponent);
      
      // 5. 执行对决
      const duelResult = executeDuel(provinceKey, randomOpponent, currentState);
      duelResults.push(duelResult);
      
      // 6. 合并败者
      const winnerKey = duelResult.winner === "attacker" ? provinceKey : randomOpponent;
      const loserKey = duelResult.winner === "attacker" ? randomOpponent : provinceKey;
      
      currentState = mergeProvinces(winnerKey, loserKey, currentState);
    } else {
      // 随机选择一个相邻对手
      const opponent = availableOpponents[Math.floor(Math.random() * availableOpponents.length)];
      
      // 4. 配对去重
      paired.add(provinceKey);
      paired.add(opponent);
      
      // 5. 执行对决
      const duelResult = executeDuel(provinceKey, opponent, currentState);
      duelResults.push(duelResult);
      
      // 6. 合并败者
      const winnerKey = duelResult.winner === "attacker" ? provinceKey : opponent;
      const loserKey = duelResult.winner === "attacker" ? opponent : provinceKey;
      
      currentState = mergeProvinces(winnerKey, loserKey, currentState);
    }
  }
  
  // 确保每轮至少有一场对决
  // 如果没有任何对决发生但还有多个存活省份，强制随机配对一场
  const remainingAlive = getAliveProvinces(currentState);
  if (duelResults.length === 0 && remainingAlive.length > 1) {
    const attacker = remainingAlive[0];
    const defender = remainingAlive[1];
    
    const duelResult = executeDuel(attacker, defender, currentState);
    duelResults.push(duelResult);
    
    const winnerKey = duelResult.winner === "attacker" ? attacker : defender;
    const loserKey = duelResult.winner === "attacker" ? defender : attacker;
    
    currentState = mergeProvinces(winnerKey, loserKey, currentState);
  }
  
  // 更新轮次
  currentState.round++;
  
  // 记录历史
  currentState.history.push({
    round: currentState.round,
    battles: duelResults
  });
  
  return {
    gameState: currentState,
    battles: duelResults,
    round: currentState.round,
    aliveCount: getAliveProvinces(currentState).length
  };
}

// ========================================
// 导出模块（兼容不同模块系统）
// ========================================
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    dimensionNames,
    dimensionKeys,
    initGameState,
    getAliveProvinces,
    getEffectiveHeroes,
    getProvinceStats,
    getRuler,
    executeDuel,
    mergeProvinces,
    executeRound
  };
}
