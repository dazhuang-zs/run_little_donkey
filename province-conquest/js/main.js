// 主程序入口

// 全局数据引用
window.provinceData = provinceData;
window.geoNameMap = geoNameMap;

/**
 * 初始化应用
 */
async function init() {
    console.log('初始化问鼎中原...');
    
    // 初始化地图
    await window.initMap();
    
    // 绑定事件
bindEvents();
    
    // 初始化状态
    window.updateMap();
    updateStatus();
    updateHeroesList();
    
    console.log('初始化完成');
}

/**
 * 绑定按钮事件
 */
function bindEvents() {
    // 开始按钮
    document.getElementById('btnStart').addEventListener('click', function() {
        window.startConquest();
        this.textContent = '征战中...';
    });
    
    // 暂停按钮
    document.getElementById('btnPause').addEventListener('click', function() {
        if (isPaused) {
            window.resumeConquest();
            this.textContent = '暂停';
        } else {
            window.pauseConquest();
            this.textContent = '继续';
        }
    });
    
    // 重置按钮
    document.getElementById('btnReset').addEventListener('click', function() {
        window.resetConquest();
        document.getElementById('btnStart').textContent = '开始征服';
        document.getElementById('btnPause').textContent = '暂停';
    });
    
    // 速度选择
    document.getElementById('speedSelect').addEventListener('change', function() {
        window.setSpeed(parseInt(this.value));
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露isPaused变量
let isPaused = false;
Object.defineProperty(window, 'isPausedGlobal', {
    get: () => isPaused,
    set: (val) => { isPaused = val; }
});
