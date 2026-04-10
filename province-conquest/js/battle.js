// 对决计算模块

/**
 * 计算攻击方总战力
 * @param {Object} data - 省份数据
 * @returns {number} 攻击方总战力
 */
function calculateAttackerPower(data) {
    let totalPower = 0;
    let conqueredCount = 0;
    
    for (const key in data) {
        if (data[key].conquered) {
            totalPower += data[key].power;
            conqueredCount++;
        }
    }
    
    // 秦始皇基础战力 + 已征服省份加成
    const basePower = 100; // 秦始皇
    const bonus = (totalPower - basePower) * 0.3;
    
    return Math.round(basePower + bonus + totalPower * 0.1);
}

/**
 * 计算防御方战力（含主场优势）
 * @param {Object} province - 省份数据
 * @returns {number} 防御方战力
 */
function calculateDefenderPower(province) {
    const basePower = province.power;
    const homeAdvantage = 1.2; // 主场优势20%
    return Math.round(basePower * homeAdvantage);
}

/**
 * 添加随机波动
 * @param {number} power - 基础战力
 * @returns {number} 波动后战力
 */
function addRandomFactor(power) {
    const factor = 0.9 + Math.random() * 0.2; // 0.9 ~ 1.1
    return Math.round(power * factor);
}

/**
 * 执行对决
 * @param {string} targetKey - 目标省份key
 * @param {Object} data - 省份数据
 * @returns {Object} 对决结果
 */
function executeBattle(targetKey, data) {
    const target = data[targetKey];
    
    // 计算双方战力
    let attackerBasePower = calculateAttackerPower(data);
    let defenderBasePower = calculateDefenderPower(target);
    
    // 添加随机因素
    let attackerFinalPower = addRandomFactor(attackerBasePower);
    let defenderFinalPower = addRandomFactor(defenderBasePower);
    
    // 判定胜负
    const victory = attackerFinalPower > defenderFinalPower;
    
    return {
        attacker: {
            name: "秦始皇阵营",
            basePower: attackerBasePower,
            finalPower: attackerFinalPower
        },
        defender: {
            name: target.hero,
            province: target.name,
            basePower: defenderBasePower,
            finalPower: defenderFinalPower
        },
        victory: victory,
        targetKey: targetKey
    };
}

/**
 * 获取下一个可征服的相邻省份
 * @param {Object} data - 省份数据
 * @returns {string|null} 省份key或null
 */
function getNextTarget(data) {
    // 找出所有已征服省份
    const conquered = Object.keys(data).filter(k => data[k].conquered);
    
    // 找出所有相邻但未征服的省份
    const targets = [];
    for (const key of conquered) {
        const adj = data[key].adj || [];
        for (const adjKey of adj) {
            if (data[adjKey] && !data[adjKey].conquered) {
                targets.push(adjKey);
            }
        }
    }
    
    // 去重并排序（优先选择战力较低的）
    const uniqueTargets = [...new Set(targets)];
    uniqueTargets.sort((a, b) => data[a].power - data[b].power);
    
    return uniqueTargets.length > 0 ? uniqueTargets[0] : null;
}

/**
 * 检查是否已经统一
 * @param {Object} data - 省份数据
 * @returns {boolean}
 */
function checkVictory(data) {
    return Object.values(data).every(p => p.conquered);
}
