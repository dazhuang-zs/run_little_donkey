// 评论洞察助手 - 前端交互

const API_URL = '/api/analyze';

const platformNames = {
    'xiaohongshu': '小红书',
    'dianping': '大众点评',
    'douyin': '抖音'
};

// DOM 元素
const urlInput = document.getElementById('url-input');
const analyzeBtn = document.getElementById('analyze-btn');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const error = document.getElementById('error');
const errorMessage = document.getElementById('error-message');

// 绑定事件
analyzeBtn.addEventListener('click', analyze);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') analyze();
});

// 分析函数
async function analyze() {
    const url = urlInput.value.trim();
    
    if (!url) {
        showError('请输入分享链接');
        return;
    }
    
    // 显示加载状态
    showLoading();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        displayResult(data);
        
    } catch (err) {
        showError('网络错误，请稍后重试');
        console.error(err);
    }
}

// 显示结果
function displayResult(data) {
    hideAll();
    
    // 平台信息
    document.getElementById('platform-badge').textContent = platformNames[data.platform] || data.platform;
    document.getElementById('content-id').textContent = `ID: ${data.content_id}`;
    
    // 情感分析
    const sentiment = data.sentiment;
    document.getElementById('positive-count').textContent = sentiment.positive + '%';
    document.getElementById('neutral-count').textContent = sentiment.neutral + '%';
    document.getElementById('negative-count').textContent = sentiment.negative + '%';
    
    // 有用总结
    renderList('summary-list', data.summary);
    
    // 避坑指南
    renderList('pitfalls-list', data.pitfalls);
    
    // 待确认
    renderList('uncertain-list', data.uncertain);
    
    // 显示结果区域
    result.classList.remove('hidden');
}

// 渲染列表
function renderList(elementId, items) {
    const list = document.getElementById(elementId);
    list.innerHTML = items.map(item => `<li>${item}</li>`).join('');
}

// 显示加载
function showLoading() {
    hideAll();
    loading.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

// 显示错误
function showError(message) {
    hideAll();
    errorMessage.textContent = message;
    error.classList.remove('hidden');
    analyzeBtn.disabled = false;
}

// 隐藏所有
function hideAll() {
    loading.classList.add('hidden');
    result.classList.add('hidden');
    error.classList.add('hidden');
}

// 复制结果
document.getElementById('copy-btn').addEventListener('click', () => {
    const summary = document.getElementById('summary-list').textContent;
    const pitfalls = document.getElementById('pitfalls-list').textContent;
    const uncertain = document.getElementById('uncertain-list').textContent;
    
    const text = `【评论洞察分析】

✅ 有用总结：
${summary}

⚠️ 避坑指南：
${pitfalls}

❓ 待确认：
${uncertain}`;
    
    navigator.clipboard.writeText(text).then(() => {
        alert('已复制到剪贴板');
    });
});

// 新分析
document.getElementById('new-analysis-btn').addEventListener('click', () => {
    urlInput.value = '';
    hideAll();
    analyzeBtn.disabled = false;
    urlInput.focus();
});

// 回车自动聚焦
urlInput.focus();