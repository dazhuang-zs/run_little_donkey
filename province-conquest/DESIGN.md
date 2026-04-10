# 问鼎中原 - 省份争霸动画视频

## 项目概述
纯地图色块扩张动画视频。34个省级行政区各有独立颜色，每省拥有不固定数量的古代名人，6维属性（统帅/武力/智谋/政治/魅力/技艺）相加后与邻省分维度对决。被征服省颜色统一为征服者色，最终一省独占全国。自动播放，无交互。

## 主要特性
- **左右分栏布局**：左侧78%地图 + 右侧22% PK展示区（移动端自动切换为上下布局65%/35%）
- **并发PK对决**：每轮所有存活省份同时与随机邻省对决，右侧实时展示所有对决详情
- **六维可视化对比**：对决面板展示双方省份名（彩色）、6维度对比条、比分及胜方标签
- **名人卡片展示**：按省份分组展示参战名人（姓名、称号、6维属性标签，属性颜色区分）
- **颜色感染动画**：胜利省份颜色渐变感染失败省份
- **战斗记录**：右侧保留最近30条历史对决记录
- **可扩展架构**：预留技能系统（skills）和省份增益（buffs）接口

## 技术栈
- 纯HTML/CSS/JS，无框架依赖
- ECharts 5（中国地图渲染）
- 阿里DataV GeoJSON数据源

## 文件结构
- `index.html` — 页面布局（左右分栏：地图区 + PK展示区）
- `css/style.css` — 样式（深色主题 + 分栏布局 + 对决面板 + 名人卡片 + 动画效果）
- `js/data.js` — 34省数据 + 邻接关系 + 扩展接口（skills/buffs预留）
- `js/battle.js` — 分维度对决引擎 + 全局混战轮次
- `js/map.js` — ECharts地图渲染 + 征服动画 + 颜色渐变
- `js/animation.js` — 自动播放动画控制器（入口）+ 右侧PK区DOM渲染
- `PK-RULES.md` — 详细PK对决规则说明（如有）

## 页面布局

### 整体结构
```
┌──────────────────────────────────┬────────────┐
│          地图区域 (78%)          │  PK区 (22%) │
│                                  │            │
│         ECharts 中国地图         │  对决列表   │
│         (叠加标题浮层)           │  名人列表   │
│                                  │  战斗记录   │
└──────────────────────────────────┴────────────┘
```

### 左侧地图区（78%）
- ECharts渲染的中国省级地图
- 顶部叠加标题浮层（"问鼎中原" + 副标题）
- 交战省份金色边框闪烁高亮
- 征服时颜色渐变动画

### 右侧PK展示区（22%）
分为三个子区域，从上到下依次为：

1. **对决列表**（`#battlesList`）
   - 每条对决项包含：
     - 双方省份名（使用省份对应颜色显示）
     - VS徽章
     - 6维度对比条（统/武/智/政/魅/技），每条显示双方数值 + 比例条
     - 胜出维度高亮（`.win`标记）
     - 比分（如 4:2）+ 胜方标签

2. **名人列表**（`#heroesList`）
   - 按省份分组展示所有存活省份的名人
   - 每个分组包含：省份色点 + 省份名 + 人数
   - 每张名人卡片包含：姓名、称号、6维属性标签
   - 属性标签颜色区分：统红/武橙/智蓝/政绿/魅紫/技黄

3. **战斗记录**（`#historyList`）
   - 最近30条历史对决记录
   - 格式：胜方 → 败方

### 移动端适配
- 自动切换为上下布局：地图65% + PK区35%

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
- 每轮所有存活省份同时与随机邻省对决（并发PK）
- 6维度逐一比较，赢多者胜
- 3:3平局比总和，总和相同攻方胜
- 胜方吸收败方所有名人
- 详细PK规则请参见 [PK-RULES.md](PK-RULES.md)

### 动画流程
每轮动画按以下序列执行：

1. **执行对决** — 调用 `executeRound()` 计算所有存活省份的并发对决结果
2. **展示对决详情** — `updateBattlesList()` 渲染右侧对决列表（6维对比条 + 比分）；`updateHeroesList()` 更新名人分组卡片
3. **高亮交战省份** — `highlightAllBattleProvinces()` 为所有交战省份添加金色边框闪烁动画（500ms间隔）
4. **观察等待** — 停顿2秒供观众查看
5. **颜色渐变感染** — 所有失败省份同时播放征服动画（`animateConquest()`），颜色渐变为胜者色
6. **更新记录** — `addHistoryRecord()` 将本轮结果追加到战斗记录
7. **取消高亮 + 刷新地图** — 清除闪烁、`updateMapColors()` 刷新全局颜色
8. **轮间停顿** — 800ms后进入下一轮

### 胜利画面
当仅剩一个存活省份时触发：
- 全屏浮层展示冠军省份名称
- 雷达图展示冠军省份综合属性
- 滚动展示所有收编的名人

## 扩展接口

### 新增人物

**方式一：直接在数据中添加**

在 `js/data.js` 的对应省份 `heroes` 数组中添加新人物对象即可，`createHero()` 工厂函数会自动补全缺省字段（包括 `skills: []` 和 `id: null`）：
```javascript
// 在 provinceData 的某省 heroes 数组中新增：
{ name: "新人物名", title: "新称号", stats: { command: 80, martial: 75, wisdom: 90, politics: 85, charisma: 70, craft: 60 } }
```

**方式二：运行时动态添加**

使用 `addHeroToProvince()` 工具函数在运行时添加：
```javascript
addHeroToProvince('henan', {
  name: "新人物名",
  title: "新称号",
  stats: { command: 80, martial: 75, wisdom: 90, politics: 85, charisma: 70, craft: 60 },
  skills: []  // 可选，默认为空数组
});
```

> **无需修改 battle.js 或 animation.js**——两者均通过动态遍历 heroes 数组工作，不硬编码人物数量。

### 调整属性值

直接修改名人 `stats` 对象中的数值即可，battle.js 的 `getProvinceStats()` 会动态求和，`executeDuel()` 会正确比较新数值。无需修改任何其他文件。

### 新增省份

在 `js/data.js` 的 `provinceData` 对象中使用 `createProvince()` 工厂函数添加：
```javascript
newProvince: createProvince({
  name: "新省份名",
  color: "#颜色代码",
  heroes: [
    { name: "人物名", title: "称号", stats: { command: 80, martial: 75, wisdom: 90, politics: 85, charisma: 70, craft: 60 } }
  ],
  adj: ["相邻省份key1", "相邻省份key2"],
  buffs: []
})
```
同时在 `geoNameMap` 中添加中文名到key的映射关系。也可以使用 `addProvince()` 运行时添加。

### 技能系统（预留）

**当前状态：字段已预留，处理逻辑尚未实现。**

- `data.js`：每个人物通过 `createHero()` 自动拥有 `skills: []` 字段；已定义 `SKILL_TYPES`（passive/active）枚举。
- `battle.js`：**当前未包含技能处理逻辑**。后续实现时建议在 `executeDuel()` 的维度比较前/后增加技能触发钩子。
- `animation.js`：无需修改，技能效果体现在数值层面。

人物技能数据结构预留格式：
```javascript
skills: [
  {
    name: "技能名",
    type: "passive",   // passive | active
    effect: null        // 待实现：技能效果函数
  }
]
```

### 省份Buff系统（预留）

**当前状态：字段已预留，处理逻辑尚未实现。**

- `data.js`：每个省份通过 `createProvince()` 自动拥有 `buffs: []` 字段。
- `battle.js`：**当前未包含Buff处理逻辑**。后续实现时建议在 `getProvinceStats()` 计算总和后叠加Buff加成。

Buff数据结构预留格式：
```javascript
buffs: [
  {
    name: "Buff名称",
    target: "command",  // 影响的维度
    value: 10           // 加成数值
  }
]
```

## 使用方式
直接用浏览器打开 index.html，动画自动播放。
