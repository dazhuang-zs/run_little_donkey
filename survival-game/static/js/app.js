/**
 * 重生之月薪2000 - 前端应用
 * 处理用户交互、游戏逻辑和API通信
 */

// API 基础URL
const API_BASE_URL = '/api/v1';

// 全局状态
let currentToken = null;
let currentGameState = null;
let currentPlayer = null;

// DOM 元素
const elements = {
    // 页面
    authPage: document.getElementById('auth-page'),
    gamePage: document.getElementById('game-page'),
    endingPage: document.getElementById('ending-page'),
    
    // 认证
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    loginUsername: document.getElementById('login-username'),
    loginPassword: document.getElementById('login-password'),
    registerUsername: document.getElementById('register-username'),
    registerEmail: document.getElementById('register-email'),
    registerPassword: document.getElementById('register-password'),
    loginBtn: document.getElementById('login-btn'),
    registerBtn: document.getElementById('register-btn'),
    loginError: document.getElementById('login-error'),
    registerError: document.getElementById('register-error'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    
    // 游戏
    playerName: document.getElementById('player-name'),
    logoutBtn: document.getElementById('logout-btn'),
    dayNum: document.getElementById('day-num'),
    timeOfDay: document.getElementById('time-of-day'),
    money: document.getElementById('money'),
    health: document.getElementById('health'),
    healthBar: document.getElementById('health-bar'),
    stress: document.getElementById('stress'),
    stressBar: document.getElementById('stress-bar'),
    hunger: document.getElementById('hunger'),
    hungerBar: document.getElementById('hunger-bar'),
    energy: document.getElementById('energy'),
    energyBar: document.getElementById('energy-bar'),
    jobLevel: document.getElementById('job-level'),
    jobSatisfaction: document.getElementById('job-satisfaction'),
    relationship: document.getElementById('relationship'),
    
    // 事件
    eventPanel: document.getElementById('event-panel'),
    eventTitle: document.getElementById('event-title'),
    eventDescription: document.getElementById('event-description'),
    eventChoices: document.getElementById('event-choices'),
    
    // 行动
    actionsPanel: document.getElementById('actions-panel'),
    actionsGrid: document.getElementById('actions-grid'),
    startGamePanel: document.getElementById('start-game-panel'),
    startGameBtn: document.getElementById('start-game-btn'),
    
    // 日志
    logContent: document.getElementById('log-content'),
    
    // 结局
    endingTitle: document.getElementById('ending-title'),
    endingDescription: document.getElementById('ending-description'),
    endingDays: document.getElementById('ending-days'),
    endingMoney: document.getElementById('ending-money'),
    restartBtn: document.getElementById('restart-btn'),
};

// ==================== API 请求工具 ====================

async function apiRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    if (currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers,
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error?.message || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}

// ==================== 认证功能 ====================

async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });
    
    const data = await response.json();
    
    if (!response.ok || !data.success) {
        throw new Error(data.error?.message || '登录失败');
    }
    
    return data.data;
}

async function register(username, email, password) {
    const data = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
    });
    
    return data.data;
}

// ==================== 游戏功能 ====================

async function startGame() {
    const data = await apiRequest('/game/start', {
        method: 'POST',
    });
    
    currentGameState = data.data;
    return data.data;
}

async function getGameState() {
    const data = await apiRequest('/game/state');
    
    if (data.data?.game_state) {
        currentGameState = data.data.game_state;
    }
    
    return data.data;
}

async function executeAction(actionCode) {
    const data = await apiRequest('/game/action', {
        method: 'POST',
        body: JSON.stringify({ action_code: actionCode }),
    });
    
    return data.data;
}

async function getAvailableActions() {
    const data = await apiRequest('/game/available-actions');
    return data.data || [];
}

async function getCurrentEvent() {
    const data = await apiRequest('/events/current');
    return data.data;
}

async function processEventChoice(choiceId) {
    const data = await apiRequest('/events/choose', {
        method: 'POST',
        body: JSON.stringify({ choice_id: choiceId }),
    });
    
    return data.data;
}

// ==================== UI 更新 ====================

function showPage(pageName) {
    elements.authPage.classList.add('hidden');
    elements.gamePage.classList.add('hidden');
    elements.endingPage.classList.add('hidden');
    
    if (pageName === 'auth') {
        elements.authPage.classList.remove('hidden');
    } else if (pageName === 'game') {
        elements.gamePage.classList.remove('hidden');
    } else if (pageName === 'ending') {
        elements.endingPage.classList.remove('hidden');
    }
}

function updateResourceDisplay(state) {
    elements.dayNum.textContent = state.day || 1;
    elements.timeOfDay.textContent = state.time_of_day || '早晨';
    elements.money.textContent = state.money || 0;
    
    elements.health.textContent = state.health || 0;
    elements.healthBar.style.width = `${state.health || 0}%`;
    
    elements.stress.textContent = state.stress || 0;
    elements.stressBar.style.width = `${state.stress || 0}%`;
    
    elements.hunger.textContent = state.hunger || 0;
    elements.hungerBar.style.width = `${state.hunger || 0}%`;
    
    elements.energy.textContent = state.energy || 0;
    elements.energyBar.style.width = `${state.energy || 0}%`;
    
    // 工作信息
    const jobLevels = ['实习生', '初级员工', '中级员工', '高级员工', '主管', '经理', '总监'];
    elements.jobLevel.textContent = jobLevels[state.job_level - 1] || '实习生';
    elements.jobSatisfaction.textContent = state.job_satisfaction || 0;
    elements.relationship.textContent = state.relationship || 0;
}

function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[第${currentGameState?.day || 1}天] ${message}`;
    elements.logContent.appendChild(entry);
    elements.logContent.scrollTop = elements.logContent.scrollHeight;
}

function renderActions(actions) {
    elements.actionsGrid.innerHTML = '';
    
    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.disabled = !action.can_execute;
        
        const costText = [];
        if (action.cost_energy > 0) costText.push(`⚡${action.cost_energy}`);
        if (action.cost_money > 0) costText.push(`💰${action.cost_money}`);
        
        btn.innerHTML = `
            <span class="action-name">${action.name}</span>
            <span class="action-cost">${costText.join(' ')}</span>
        `;
        
        if (action.can_execute) {
            btn.addEventListener('click', () => handleAction(action.code));
        } else {
            btn.title = action.reason || '无法执行';
        }
        
        elements.actionsGrid.appendChild(btn);
    });
}

function renderEvent(event) {
    if (!event) {
        elements.eventPanel.classList.add('hidden');
        elements.actionsPanel.classList.remove('hidden');
        return;
    }
    
    elements.eventPanel.classList.remove('hidden');
    elements.actionsPanel.classList.add('hidden');
    
    elements.eventTitle.textContent = event.title;
    elements.eventDescription.textContent = event.description;
    
    elements.eventChoices.innerHTML = '';
    event.choices.forEach(choice => {
        const btn = document.createElement('button');
        btn.className = 'choice-btn';
        
        const effects = [];
        if (choice.effect_money) effects.push(`💰${choice.effect_money > 0 ? '+' : ''}${choice.effect_money}`);
        if (choice.effect_health) effects.push(`❤️${choice.effect_health > 0 ? '+' : ''}${choice.effect_health}`);
        if (choice.effect_stress) effects.push(`😰${choice.effect_stress > 0 ? '+' : ''}${choice.effect_stress}`);
        
        btn.innerHTML = `
            <div>${choice.choice_text}</div>
            <small style="color: #666;">${effects.join(' ')}</small>
        `;
        
        btn.addEventListener('click', () => handleEventChoice(choice.id));
        elements.eventChoices.appendChild(btn);
    });
}

// ==================== 事件处理 ====================

async function handleLogin() {
    const username = elements.loginUsername.value.trim();
    const password = elements.loginPassword.value;
    
    if (!username || !password) {
        elements.loginError.textContent = '请输入用户名和密码';
        return;
    }
    
    try {
        const data = await login(username, password);
        currentToken = data.access_token;
        currentPlayer = { username };
        
        elements.playerName.textContent = username;
        showPage('game');
        
        // 检查是否有进行中的游戏
        const gameData = await getGameState();
        if (gameData?.game_state && !gameData.game_state.is_game_over) {
            currentGameState = gameData.game_state;
            updateResourceDisplay(currentGameState);
            elements.startGamePanel.classList.add('hidden');
            await refreshActions();
        } else {
            elements.startGamePanel.classList.remove('hidden');
        }
    } catch (error) {
        elements.loginError.textContent = error.message;
    }
}

async function handleRegister() {
    const username = elements.registerUsername.value.trim();
    const email = elements.registerEmail.value.trim();
    const password = elements.registerPassword.value;
    
    if (!username || !password) {
        elements.registerError.textContent = '请输入用户名和密码';
        return;
    }
    
    try {
        await register(username, email, password);
        
        // 自动登录
        const data = await login(username, password);
        currentToken = data.access_token;
        currentPlayer = { username };
        
        elements.playerName.textContent = username;
        showPage('game');
        elements.startGamePanel.classList.remove('hidden');
    } catch (error) {
        elements.registerError.textContent = error.message;
    }
}

async function handleStartGame() {
    try {
        const gameData = await startGame();
        currentGameState = gameData;
        updateResourceDisplay(gameData);
        
        elements.startGamePanel.classList.add('hidden');
        elements.logContent.innerHTML = '';
        addLog('游戏开始！你是一个月薪2000的实习生...', 'success');
        
        await refreshActions();
    } catch (error) {
        addLog(`开始游戏失败: ${error.message}`, 'danger');
    }
}

async function handleAction(actionCode) {
    try {
        const result = await executeAction(actionCode);
        
        if (result.success) {
            currentGameState = result.data.updated_game_state;
            updateResourceDisplay(currentGameState);
            
            const actionResult = result.data.action_result;
            addLog(`执行了"${actionResult.action_name}"`, 'success');
            
            // 检查是否触发结局
            if (result.data.triggered_ending) {
                showEnding(result.data.triggered_ending);
                return;
            }
            
            // 检查是否触发事件
            const event = await getCurrentEvent();
            if (event) {
                renderEvent(event);
            } else {
                await refreshActions();
            }
        } else {
            addLog(result.message, 'warning');
        }
    } catch (error) {
        addLog(`执行失败: ${error.message}`, 'danger');
    }
}

async function handleEventChoice(choiceId) {
    try {
        const result = await processEventChoice(choiceId);
        
        if (result.success) {
            currentGameState = result.data.updated_game_state;
            updateResourceDisplay(currentGameState);
            
            addLog('做出了选择...', 'success');
            
            // 检查是否触发结局
            if (result.data.triggered_ending) {
                showEnding(result.data.triggered_ending);
                return;
            }
            
            renderEvent(null);
            await refreshActions();
        }
    } catch (error) {
        addLog(`选择处理失败: ${error.message}`, 'danger');
    }
}

async function refreshActions() {
    try {
        const actions = await getAvailableActions();
        renderActions(actions);
    } catch (error) {
        console.error('获取动作列表失败:', error);
    }
}

function showEnding(ending) {
    elements.endingTitle.textContent = ending.title;
    elements.endingDescription.textContent = ending.description;
    elements.endingDays.textContent = currentGameState?.day || 0;
    elements.endingMoney.textContent = currentGameState?.money || 0;
    
    showPage('ending');
}

function handleLogout() {
    currentToken = null;
    currentGameState = null;
    currentPlayer = null;
    
    elements.loginUsername.value = '';
    elements.loginPassword.value = '';
    elements.loginError.textContent = '';
    
    showPage('auth');
}

function handleRestart() {
    showPage('game');
    elements.startGamePanel.classList.remove('hidden');
    elements.logContent.innerHTML = '';
}

// ==================== 初始化 ====================

function init() {
    // 标签切换
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const tab = btn.dataset.tab;
            if (tab === 'login') {
                elements.loginForm.classList.remove('hidden');
                elements.registerForm.classList.add('hidden');
            } else {
                elements.loginForm.classList.add('hidden');
                elements.registerForm.classList.remove('hidden');
            }
        });
    });
    
    // 按钮事件
    elements.loginBtn.addEventListener('click', handleLogin);
    elements.registerBtn.addEventListener('click', handleRegister);
    elements.logoutBtn.addEventListener('click', handleLogout);
    elements.startGameBtn.addEventListener('click', handleStartGame);
    elements.restartBtn.addEventListener('click', handleRestart);
    
    // 回车键登录
    elements.loginPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    
    elements.registerPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleRegister();
    });
}

// 启动应用
document.addEventListener('DOMContentLoaded', init);
