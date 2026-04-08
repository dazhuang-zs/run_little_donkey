// 动画控制模块

let isRunning = false;
let isPaused = false;
let currentStageIndex = 0;
let animationSpeed = 2000;

/**
 * 设置动画速度
 */
function setSpeed(speed) {
    animationSpeed = speed;
}

/**
 * 开始征服动画
 */
async function startConquest() {
    if (isRunning) return;
    
    isRunning = true;
    isPaused = false;
    
    updateButtons();
    await runConquestLoop();
}

/**
 * 暂停动画
 */
function pauseConquest() {
    isPaused = true;
    updateButtons();
}

/**
 * 继续动画
 */
function resumeConquest() {
    isPaused = false;
    updateButtons();
    runConquestLoop();
}

/**
 * 重置动画
 */
function resetConquest() {
    isRunning = false;
    isPaused = false;
    currentStageIndex = 0;
    
    // 重置省份状态
    for (const key in window.provinceData) {
        window.provinceData[key].conquered = (key === 'shaanxi');
    }
    
    // 更新UI
    window.updateMap();
    updateStatus();
    clearLog();
    clearBattlePanel();
    
    // 重置英雄榜
    updateHeroesList();
    
    updateButtons();
}

/**
 * 征服主循环
 */
async function runConquestLoop() {
    while (isRunning && !checkVictory(window.provinceData)) {
        if (isPaused) return;
        
        // 获取下一个目标
        const targetKey = getNextTarget(window.provinceData);
        if (!targetKey) {
            showVictory();
            break;
        }
        
        // 执行对决
        const currentStage = getCurrentStage();
        document.getElementById('currentStage').textContent = currentStage;
        
        await conquerProvince(targetKey);
        
        // 等待
        await sleep(animationSpeed);
    }
    
    if (checkVictory(window.provinceData)) {
        showVictory();
    }
}

/**
 * 征服单个省份
 */
async function conquerProvince(targetKey) {
    const target = window.provinceData[targetKey];
    
    // 显示对决面板
    showBattlePanel(targetKey);
    
    // 高亮目标省份
    window.highlightProvince(targetKey);
    
    await sleep(500);
    
    // 执行对决计算
    const result = executeBattle(targetKey, window.provinceData);
    
    // 更新对决面板
    updateBattleResult(result);
    
    await sleep(800);
    
    if (result.victory) {
        // 征服成功
        window.provinceData[targetKey].conquered = true;
        window.updateMap();
        
        // 添加日志
        addLog(`✅ 征服 ${target.name}！${target.hero} 归顺秦始皇阵营`);
        
        // 更新英雄榜
        updateHeroesList();
    } else {
        // 征服失败（这里简化处理，确保一定能征服）
        addLog(`⚠️ ${target.name} 抵抗顽强，再次进攻...`);
        // 实际上重新尝试
        window.provinceData[targetKey].conquered = true;
        window.updateMap();
        updateHeroesList();
    }
    
    // 更新状态
    updateStatus();
}

/**
 * 显示对决面板
 */
function showBattlePanel(targetKey) {
    const target = window.provinceData[targetKey];
    const panel = document.getElementById('battlePanel');
    
    panel.classList.remove('hidden');
    
    document.getElementById('attackerName').textContent = '秦始皇';
    document.getElementById('attackerProvince').textContent = '陕西';
    document.getElementById('defenderName').textContent = target.hero;
    document.getElementById('defenderProvince').textContent = target.name;
    
    document.getElementById('attackerPower').textContent = calculateAttackerPower(window.provinceData);
    document.getElementById('defenderPower').textContent = calculateDefenderPower(target);
}

/**
 * 更新对决结果
 */
function updateBattleResult(result) {
    const resultDiv = document.getElementById('battleResult');
    
    document.getElementById('attackerPower').textContent = result.attacker.finalPower;
    document.getElementById('defenderPower').textContent = result.defender.finalPower;
    
    if (result.victory) {
        resultDiv.textContent = '🎉 胜利！征服成功！';
        resultDiv.className = 'battle-result';
    } else {
        resultDiv.textContent = '⚔️ 对方抵抗顽强...';
        resultDiv.className = 'battle-result defeat';
    }
}

/**
 * 清除对决面板
 */
function clearBattlePanel() {
    document.getElementById('battlePanel').classList.add('hidden');
    document.getElementById('battleResult').textContent = '';
}

/**
 * 更新状态显示
 */
function updateStatus() {
    let count = 0;
    let totalPower = 0;
    
    for (const key in window.provinceData) {
        if (window.provinceData[key].conquered) {
            count++;
            totalPower += window.provinceData[key].power;
        }
    }
    
    document.getElementById('conqueredCount').textContent = count;
    document.getElementById('totalPower').textContent = totalPower;
}

/**
 * 更新英雄榜
 */
function updateHeroesList() {
    const list = document.getElementById('heroesList');
    list.innerHTML = '';
    
    const heroes = [];
    for (const key in window.provinceData) {
        if (window.provinceData[key].conquered) {
            heroes.push({
                name: window.provinceData[key].hero,
                province: window.provinceData[key].name,
                type: window.provinceData[key].type
            });
        }
    }
    
    for (const hero of heroes) {
        const item = document.createElement('div');
        item.className = 'hero-item';
        item.innerHTML = `
            <span class="hero-name">${hero.name}</span>
            <span class="hero-title">${hero.province} · ${hero.type}</span>
        `;
        list.appendChild(item);
    }
}

/**
 * 获取当前阶段
 */
function getCurrentStage() {
    let count = 0;
    for (const key in window.provinceData) {
        if (window.provinceData[key].conquered) count++;
    }
    
    if (count <= 5) return '西北统一';
    if (count <= 10) return '南下蜀地';
    if (count <= 15) return '西南平定';
    if (count <= 20) return '华南进取';
    if (count <= 25) return '东进中原';
    if (count <= 30) return '燕赵之战';
    return '关外征伐';
}

/**
 * 添加日志
 */
function addLog(message) {
    const log = document.getElementById('conquestLog');
    const item = document.createElement('div');
    item.className = 'log-item';
    const time = new Date().toLocaleTimeString();
    item.textContent = `[${time}] ${message}`;
    log.insertBefore(item, log.firstChild);
}

/**
 * 清除日志
 */
function clearLog() {
    document.getElementById('conquestLog').innerHTML = '';
}

/**
 * 显示胜利
 */
function showVictory() {
    isRunning = false;
    updateButtons();
    
    addLog('🏆 天下一统！秦始皇完成霸业！');
    document.getElementById('currentStage').textContent = '天下一统';
    
    // 可以添加庆祝动画
}

/**
 * 更新按钮状态
 */
function updateButtons() {
    document.getElementById('btnStart').disabled = isRunning;
    document.getElementById('btnPause').disabled = !isRunning || isPaused;
    document.getElementById('btnReset').disabled = isRunning && !isPaused;
}

/**
 * 睡眠函数
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 导出函数
window.setSpeed = setSpeed;
window.startConquest = startConquest;
window.pauseConquest = pauseConquest;
window.resumeConquest = resumeConquest;
window.resetConquest = resetConquest;
