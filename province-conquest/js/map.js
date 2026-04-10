// ========================================
// 地图模块 - 省份争霸
// ========================================

let chart = null;
let geoJson = null;
let battleHighlightTimer = null;

/**
 * 初始化地图
 * @returns {Promise<Object>} chart实例
 */
async function initMap() {
    const chartDom = document.getElementById('chinaMap');
    if (!chartDom) {
        console.error('找不到地图容器 #chinaMap');
        return null;
    }

    chart = echarts.init(chartDom, 'dark');

    // 加载中国地图GeoJSON
    try {
        const response = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json');
        geoJson = await response.json();
        echarts.registerMap('china', geoJson);
    } catch (error) {
        console.warn('在线地图加载失败，尝试本地备用:', error);
        try {
            const response = await fetch('assets/china.json');
            geoJson = await response.json();
            echarts.registerMap('china', geoJson);
        } catch (e) {
            console.error('地图加载失败:', e);
            chartDom.innerHTML = '<p style="text-align:center;padding:50px;color:#fff;">地图加载失败，请刷新页面重试</p>';
            return null;
        }
    }

    // 渲染初始地图
    renderInitialMap();

    return chart;
}

/**
 * 渲染初始地图
 */
function renderInitialMap() {
    const data = [];

    for (const key in provinceData) {
        const p = provinceData[key];
        data.push({
            name: p.name,
            value: p.heroes.length,
            key: key,
            itemStyle: {
                areaColor: p.color,
                borderColor: '#1a1a2e',
                borderWidth: 1
            }
        });
    }

    const option = {
        backgroundColor: 'transparent',
        series: [{
            type: 'map',
            map: 'china',
            roam: false,
            zoom: 1.2,
            center: [104, 35],
            label: {
                show: true,
                color: '#fff',
                fontSize: 10,
                formatter: function(params) {
                    return params.name;
                }
            },
            itemStyle: {
                borderColor: '#1a1a2e',
                borderWidth: 1
            },
            emphasis: {
                disabled: true
            },
            data: data
        }]
    };

    chart.setOption(option);
}

/**
 * 更新地图颜色
 * @param {Object} gameState - 游戏状态对象
 * @param {Object} gameState.provinces - 省份状态 { [key]: { owner: string|null, heroes: [] } }
 */
function updateMapColors(gameState) {
    if (!chart) return;

    const data = [];

    for (const key in provinceData) {
        const p = provinceData[key];
        const state = gameState.provinces[key];
        let color = p.color;
        let heroCount = p.heroes.length;

        // 如果已被征服，使用最终统治者的颜色
        if (state && state.conquered) {
            const rulerKey = getRuler(key, gameState);
            if (rulerKey && rulerKey !== key) {
                const rulerProvince = provinceData[rulerKey];
                if (rulerProvince) {
                    color = rulerProvince.color;
                }
            }
            heroCount = (state.heroes ? state.heroes.length : 0) +
                        (state.absorbedHeroes ? state.absorbedHeroes.length : 0);
        }

        data.push({
            name: p.name,
            value: heroCount,
            key: key,
            itemStyle: {
                areaColor: color,
                borderColor: '#1a1a2e',
                borderWidth: 1
            },
            label: {
                show: true,
                formatter: params => {
                    return params.name;
                }
            }
        });
    }

    chart.setOption({
        series: [{
            data: data
        }]
    });
}

/**
 * 高亮所有交战省份（不降低其他省份亮度）
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
    battleHighlightTimer = setInterval(() => {
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

/**
 * 征服动画（颜色渐变）
 * @param {string} winnerKey - 胜利方省份key
 * @param {string} loserKey - 失败方省份key
 * @param {Object} gameState - 游戏状态
 * @param {string} loserColor - 失败省份原来的颜色（用于动画开始时显示）
 * @returns {Promise<void>}
 */
function animateConquest(winnerKey, loserKey, gameState, loserColor) {
    return new Promise((resolve) => {
        if (!chart) {
            resolve();
            return;
        }

        const winnerProvince = provinceData[winnerKey];
        const winnerColor = winnerProvince.color;

        // 计算失败省份的当前颜色（考虑可能已被征服）
        let currentLoserColor = provinceData[loserKey].color;
        const loserState = gameState.provinces[loserKey];
        if (loserState && loserState.conquered) {
            const rulerKey = getRuler(loserKey, gameState);
            if (rulerKey && rulerKey !== loserKey) {
                const rulerProvince = provinceData[rulerKey];
                if (rulerProvince) {
                    currentLoserColor = rulerProvince.color;
                }
            }
        }

        const data = [];
        for (const key in provinceData) {
            const p = provinceData[key];
            const state = gameState.provinces[key];
            let color = p.color;

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

            // 失败省份使用当前颜色（动画开始时会显示这个颜色）
            if (key === loserKey) {
                color = currentLoserColor;
            }

            data.push({
                name: p.name,
                value: key === loserKey ? 0 : (state?.heroes?.length || p.heroes.length),
                key: key,
                itemStyle: {
                    areaColor: color,
                    borderColor: '#1a1a2e',
                    borderWidth: 1
                },
                label: {
                    show: true,
                    formatter: params => params.name
                }
            });
        }

        // 第一阶段：设置初始状态（失败省份显示当前颜色）
        chart.setOption({
            series: [{
                data: data,
                animationDuration: 0
            }]
        });

        // 第二阶段：失败省份颜色渐变为胜利者颜色
        setTimeout(() => {
            const newData = data.map(item => {
                if (item.key === loserKey) {
                    return {
                        ...item,
                        itemStyle: {
                            ...item.itemStyle,
                            areaColor: winnerColor,
                            borderColor: '#ffd700', // 高亮边框
                            borderWidth: 3
                        }
                    };
                }
                return item;
            });

            chart.setOption({
                series: [{
                    data: newData,
                    animationDuration: 1500,
                    animationEasing: 'cubicOut'
                }]
            });

            // 动画完成后resolve
            setTimeout(() => {
                resolve();
            }, 1500);
        }, 100);
    });
}

/**
 * 最终胜利雷达图
 * @param {string} championKey - 冠军省份key
 * @param {Object} gameState - 游戏状态
 */
function renderVictoryRadar(championKey, gameState) {
    const radarDom = document.getElementById('victoryRadar');
    if (!radarDom) {
        console.error('找不到雷达图容器 #victoryRadar');
        return;
    }

    const radarChart = echarts.init(radarDom, 'dark');
    const championProvince = provinceData[championKey];
    const state = gameState.provinces[championKey];
    // 合并原始英雄和吸收的英雄
    const allHeroes = [...(state && state.heroes ? state.heroes : championProvince.heroes || []),
                       ...(state && state.absorbedHeroes ? state.absorbedHeroes : [])];
    const heroes = allHeroes;

    // 计算六维平均值
    const dimensions = ['统帅', '武力', '智谋', '政治', '魅力', '技艺'];
    const statKeys = ['command', 'martial', 'wisdom', 'politics', 'charisma', 'craft'];

    const avgValues = statKeys.map(statKey => {
        const sum = heroes.reduce((acc, hero) => acc + (hero.stats[statKey] || 0), 0);
        return Math.round(sum / heroes.length);
    });

    // 计算最大值用于展示
    const maxValues = statKeys.map(statKey => {
        return Math.max(...heroes.map(hero => hero.stats[statKey] || 0));
    });

    const option = {
        backgroundColor: 'transparent',
        title: {
            text: championProvince.name + ' - 综合实力',
            left: 'center',
            top: 10,
            textStyle: {
                color: '#ffd700',
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'item'
        },
        radar: {
            indicator: dimensions.map((dim, i) => ({
                name: dim,
                max: 100
            })),
            center: ['50%', '55%'],
            radius: '65%',
            axisName: {
                color: '#ffd700',
                fontSize: 12
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(255, 215, 0, 0.05)', 'rgba(255, 215, 0, 0.1)',
                            'rgba(255, 215, 0, 0.15)', 'rgba(255, 215, 0, 0.2)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 215, 0, 0.3)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255, 215, 0, 0.3)'
                }
            }
        },
        series: [{
            type: 'radar',
            data: [
                {
                    value: avgValues,
                    name: '平均值',
                    areaStyle: {
                        color: 'rgba(255, 215, 0, 0.3)'
                    },
                    lineStyle: {
                        color: '#ffd700',
                        width: 2
                    },
                    itemStyle: {
                        color: '#ffd700'
                    }
                },
                {
                    value: maxValues,
                    name: '最高值',
                    areaStyle: {
                        color: 'rgba(255, 140, 0, 0.2)'
                    },
                    lineStyle: {
                        color: '#ff8c00',
                        width: 2,
                        type: 'dashed'
                    },
                    itemStyle: {
                        color: '#ff8c00'
                    }
                }
            ]
        }],
        legend: {
            data: ['平均值', '最高值'],
            bottom: 10,
            textStyle: {
                color: '#ffd700'
            }
        }
    };

    radarChart.setOption(option);

    // 保存到全局以便后续访问
    window.victoryRadarChart = radarChart;
}

/**
 * 窗口大小改变时重新调整图表
 */
function resizeMap() {
    if (chart) {
        chart.resize();
    }
    if (window.victoryRadarChart) {
        window.victoryRadarChart.resize();
    }
}

// 监听窗口大小变化
window.addEventListener('resize', resizeMap);

// 导出函数到全局
window.initMap = initMap;
window.updateMapColors = updateMapColors;
window.highlightBattleProvinces = highlightAllBattleProvinces;
window.animateConquest = animateConquest;
window.renderVictoryRadar = renderVictoryRadar;
window.resizeMap = resizeMap;
