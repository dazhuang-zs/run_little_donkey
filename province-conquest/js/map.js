// 地图模块

let chart = null;
let geoJson = null;

/**
 * 初始化地图
 */
async function initMap() {
    const chartDom = document.getElementById('chinaMap');
    chart = echarts.init(chartDom, 'dark');
    
    // 加载中国地图GeoJSON
    try {
        const response = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json');
        geoJson = await response.json();
        echarts.registerMap('china', geoJson);
        renderMap();
    } catch (error) {
        console.error('加载地图失败:', error);
        // 使用备用地图数据
        loadBackupMap();
    }
}

/**
 * 加载备用地图
 */
async function loadBackupMap() {
    try {
        const response = await fetch('assets/china.json');
        geoJson = await response.json();
        echarts.registerMap('china', geoJson);
        renderMap();
    } catch (e) {
        console.error('备用地图也加载失败');
        document.getElementById('chinaMap').innerHTML = '<p style="text-align:center;padding:50px;">地图加载失败，请刷新页面重试</p>';
    }
}

/**
 * 渲染地图
 */
function renderMap(highlightProvince = null) {
    const data = [];
    const provinceData = window.provinceData;
    
    for (const key in provinceData) {
        const p = provinceData[key];
        let itemStyle = {};
        
        if (p.conquered) {
            itemStyle = {
                areaColor: '#e94560',
                borderColor: '#fff',
                borderWidth: 1
            };
        } else if (key === highlightProvince) {
            itemStyle = {
                areaColor: '#ffd700',
                borderColor: '#fff',
                borderWidth: 2
            };
        } else {
            itemStyle = {
                areaColor: '#3d5a80',
                borderColor: '#fff',
                borderWidth: 0.5
            };
        }
        
        data.push({
            name: p.name,
            value: p.power,
            itemStyle: itemStyle,
            label: {
                show: true,
                formatter: p.hero,
                fontSize: 10,
                color: '#fff'
            }
        });
    }
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const key = geoNameMap[params.name];
                if (key && provinceData[key]) {
                    const p = provinceData[key];
                    return `<div style="padding:10px;">
                        <strong>${p.name}</strong><br/>
                        代表: ${p.hero}<br/>
                        身份: ${p.type}<br/>
                        战力: ${p.power}<br/>
                        状态: ${p.conquered ? '已征服' : '未征服'}
                    </div>`;
                }
                return params.name;
            }
        },
        series: [{
            type: 'map',
            map: 'china',
            roam: true,
            zoom: 1.2,
            data: data,
            emphasis: {
                itemStyle: {
                    areaColor: '#ff6b6b',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    fontSize: 12
                }
            }
        }]
    };
    
    chart.setOption(option);
}

/**
 * 高亮指定省份
 */
function highlightProvince(key) {
    renderMap(key);
}

/**
 * 更新地图颜色
 */
function updateMap() {
    renderMap();
}

/**
 * 显示征服动画
 */
function showConquestAnimation(targetKey, callback) {
    // 先高亮
    highlightProvince(targetKey);
    
    // 延迟后更新
    setTimeout(() => {
        window.provinceData[targetKey].conquered = true;
        updateMap();
        if (callback) callback();
    }, 1000);
}

// 导出函数
window.initMap = initMap;
window.updateMap = updateMap;
window.highlightProvince = highlightProvince;
window.showConquestAnimation = showConquestAnimation;
