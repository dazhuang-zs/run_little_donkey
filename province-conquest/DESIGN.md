# 问鼎中原 - 省份争霸动画视频

## 项目概述
纯地图色块扩张动画视频。34个省级行政区各有独立颜色，每省拥有不固定数量的古代名人，6维属性（统帅/武力/智谋/政治/魅力/技艺）相加后与邻省分维度对决。被征服省颜色统一为征服者色，最终一省独占全国。自动播放，无交互。

## 主要特性
- **全屏地图布局**：左侧70%区域展示中国地图
- **右侧PK展示区**：30%区域展示当前对决信息
- **颜色感染动画**：胜利省份颜色渐变感染失败省份
- **可扩展架构**：支持新增人物和技能系统

## 技术栈
- 纯HTML/CSS/JS，无框架依赖
- ECharts 5（中国地图渲染）
- 阿里DataV GeoJSON数据源

## 文件结构
- index.html - 页面布局（地图+右侧PK区）
- css/style.css - 样式（深色主题+动画效果）
- js/data.js - 34省数据 + 邻接关系 + 扩展接口
- js/battle.js - 分维度对决引擎 + 全局混战轮次
- js/map.js - ECharts地图渲染 + 征服动画
- js/animation.js - 自动播放动画控制器（入口）

## 核心机制

### 六维属性
统(command)、武(martial)、智(wisdom)、政(politics)、魅(charisma)、技(craft)

### 名人数据结构
```javascript
{
  name: "人物名称",
  title: "称号",
  stats: {
    command: 95,      // 统帅
    martial: 90,      // 武力
    wisdom: 85,       // 智谋
    politics: 80,     // 政治
    charisma: 92,     // 魅力
    craft: 75         // 技艺
  },
  skills: []          // 预留：技能列表
}
```

### 省份数据结构
```javascript
{
  name: "省份名称",
  color: "#e74c3c",   // 省份颜色
  heroes: [],          // 名人列表
  adj: [],             // 相邻省份key列表
  buffs: []            // 预留：省份buff
}
```

### 对决规则
- 每轮所有存活省份同时与随机邻省对决
- 6维度逐一比较，赢多者胜
- 3:3平局比总和，总和相同攻方胜
- 胜方吸收败方所有名人

## 扩展接口

### 新增人物
在 `js/data.js` 的对应省份 `heroes` 数组中添加新人物对象：
```javascript
{
  name: "新人物名",
  title: "新称号",
  stats: {
    command: 数值,
    martial: 数值,
    wisdom: 数值,
    politics: 数值,
    charisma: 数值,
    craft: 数值
  },
  skills: [
    // 预留：后续可添加技能对象
    // {
    //   name: "技能名",
    //   type: "passive|active",
    //   effect: 技能效果函数
    // }
  ]
}
```

### 新增省份
在 `js/data.js` 的 `provinceData` 对象中添加新省份：
```javascript
newProvince: {
  name: "新省份名",
  color: "#颜色代码",
  heroes: [],
  adj: ["相邻省份key1", "相邻省份key2"],
  buffs: []
}
```
同时在 `geoNameMap` 中添加映射关系。

### 技能系统（预留）
人物可以拥有技能，技能可以影响对决结果：
- **被动技能**：永久提升某属性
- **主动技能**：在特定条件下触发

技能系统的具体实现将在后续版本中完成，当前版本已预留接口。

## 使用方式
直接用浏览器打开 index.html，动画自动播放。
