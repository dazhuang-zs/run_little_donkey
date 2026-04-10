// ========================================
// 省份争霸 - 完整数据层
// ========================================

// 省份数据（含名人、颜色、邻接关系）
const provinceData = {
  // ==================== 一档省份（5-7人）====================

  // 河南 - 中原腹地，华夏文明发源地
  henan: {
    name: "河南",
    color: "#e74c3c",
    heroes: [
      { name: "诸葛亮", title: "卧龙先生", stats: { command: 92, martial: 45, wisdom: 98, politics: 96, charisma: 95, craft: 88 } },
      { name: "岳飞", title: "精忠报国", stats: { command: 98, martial: 95, wisdom: 78, politics: 50, charisma: 98, craft: 60 } },
      { name: "老子", title: "道家始祖", stats: { command: 30, martial: 20, wisdom: 100, politics: 75, charisma: 88, craft: 85 } },
      { name: "杜甫", title: "诗圣", stats: { command: 25, martial: 30, wisdom: 82, politics: 55, charisma: 75, craft: 96 } },
      { name: "商鞅", title: "变法名相", stats: { command: 65, martial: 40, wisdom: 92, politics: 98, charisma: 45, craft: 70 } },
      { name: "张衡", title: "科圣", stats: { command: 40, martial: 35, wisdom: 90, politics: 60, charisma: 70, craft: 98 } },
      { name: "吴道子", title: "画圣", stats: { command: 30, martial: 40, wisdom: 75, politics: 50, charisma: 72, craft: 97 } }
    ],
    adj: ["shanxi", "hebei", "shandong", "anhui", "hubei", "shaanxi"]
  },

  // 陕西 - 三秦大地，帝王之乡
  shaanxi: {
    name: "陕西",
    color: "#c0392b",
    heroes: [
      { name: "秦始皇", title: "千古一帝", stats: { command: 88, martial: 70, wisdom: 92, politics: 98, charisma: 85, craft: 75 } },
      { name: "白起", title: "人屠", stats: { command: 100, martial: 82, wisdom: 85, politics: 40, charisma: 55, craft: 45 } },
      { name: "司马迁", title: "史圣", stats: { command: 35, martial: 30, wisdom: 95, politics: 65, charisma: 70, craft: 96 } },
      { name: "班超", title: "西域都护", stats: { command: 90, martial: 78, wisdom: 88, politics: 75, charisma: 85, craft: 60 } },
      { name: "张骞", title: "丝路开拓者", stats: { command: 75, martial: 70, wisdom: 88, politics: 80, charisma: 90, craft: 55 } },
      { name: "颜真卿", title: "书法宗师", stats: { command: 55, martial: 60, wisdom: 80, politics: 75, charisma: 78, craft: 95 } }
    ],
    adj: ["shanxi", "henan", "hubei", "sichuan", "gansu", "ningxia", "neimenggu"]
  },

  // 山东 - 齐鲁大地，孔孟之乡
  shandong: {
    name: "山东",
    color: "#2980b9",
    heroes: [
      { name: "孙武", title: "兵圣", stats: { command: 98, martial: 75, wisdom: 96, politics: 85, charisma: 80, craft: 90 } },
      { name: "孔子", title: "至圣先师", stats: { command: 40, martial: 45, wisdom: 98, politics: 88, charisma: 95, craft: 85 } },
      { name: "孟子", title: "亚圣", stats: { command: 35, martial: 40, wisdom: 95, politics: 85, charisma: 90, craft: 75 } },
      { name: "诸葛亮", title: "卧龙", stats: { command: 92, martial: 45, wisdom: 98, politics: 96, charisma: 95, craft: 88 } },
      { name: "王羲之", title: "书圣", stats: { command: 30, martial: 35, wisdom: 82, politics: 60, charisma: 78, craft: 98 } },
      { name: "鲁班", title: "工匠祖师", stats: { command: 45, martial: 50, wisdom: 88, politics: 55, charisma: 72, craft: 100 } },
      { name: "蒲松龄", title: "聊斋先生", stats: { command: 25, martial: 30, wisdom: 85, politics: 45, charisma: 70, craft: 92 } }
    ],
    adj: ["hebei", "henan", "jiangsu"]
  },

  // 江苏 - 江淮重镇，兵仙故里
  jiangsu: {
    name: "江苏",
    color: "#3498db",
    heroes: [
      { name: "韩信", title: "兵仙", stats: { command: 100, martial: 70, wisdom: 95, politics: 30, charisma: 75, craft: 85 } },
      { name: "项羽", title: "西楚霸王", stats: { command: 92, martial: 100, wisdom: 55, politics: 35, charisma: 92, craft: 60 } },
      { name: "刘邦", title: "汉高祖", stats: { command: 85, martial: 55, wisdom: 88, politics: 95, charisma: 96, craft: 50 } },
      { name: "唐寅", title: "江南第一才子", stats: { command: 40, martial: 45, wisdom: 88, politics: 55, charisma: 85, craft: 94 } },
      { name: "徐霞客", title: "游圣", stats: { command: 55, martial: 65, wisdom: 90, politics: 45, charisma: 80, craft: 88 } },
      { name: "施耐庵", title: "水浒作者", stats: { command: 50, martial: 55, wisdom: 85, politics: 50, charisma: 72, craft: 92 } }
    ],
    adj: ["shanghai", "zhejiang", "anhui", "shandong"]
  },

  // 浙江 - 吴越故地，人杰地灵
  zhejiang: {
    name: "浙江",
    color: "#1abc9c",
    heroes: [
      { name: "勾践", title: "卧薪尝胆", stats: { command: 88, martial: 75, wisdom: 92, politics: 90, charisma: 85, craft: 70 } },
      { name: "范蠡", title: "商圣", stats: { command: 82, martial: 70, wisdom: 96, politics: 88, charisma: 88, craft: 92 } },
      { name: "孙权", title: "吴大帝", stats: { command: 85, martial: 72, wisdom: 88, politics: 90, charisma: 86, craft: 65 } },
      { name: "王阳明", title: "心学大师", stats: { command: 78, martial: 68, wisdom: 98, politics: 85, charisma: 92, craft: 88 } },
      { name: "陆游", title: "爱国诗人", stats: { command: 60, martial: 55, wisdom: 88, politics: 65, charisma: 80, craft: 92 } },
      { name: "周瑜", title: "美周郎", stats: { command: 92, martial: 75, wisdom: 90, politics: 78, charisma: 95, craft: 82 } },
      { name: "沈括", title: "科学全才", stats: { command: 55, martial: 50, wisdom: 95, politics: 75, charisma: 70, craft: 96 } }
    ],
    adj: ["shanghai", "jiangsu", "anhui", "jiangxi", "fujian"]
  },

  // 湖北 - 荆楚大地，九省通衢
  hubei: {
    name: "湖北",
    color: "#e67e22",
    heroes: [
      { name: "屈原", title: "诗祖", stats: { command: 45, martial: 40, wisdom: 92, politics: 75, charisma: 88, craft: 95 } },
      { name: "伍子胥", title: "复仇之神", stats: { command: 90, martial: 82, wisdom: 88, politics: 85, charisma: 75, craft: 60 } },
      { name: "刘秀", title: "光武帝", stats: { command: 92, martial: 85, wisdom: 90, politics: 95, charisma: 92, craft: 65 } },
      { name: "李时珍", title: "药圣", stats: { command: 40, martial: 45, wisdom: 95, politics: 55, charisma: 80, craft: 98 } },
      { name: "孟浩然", title: "山水诗人", stats: { command: 35, martial: 40, wisdom: 85, politics: 50, charisma: 78, craft: 90 } },
      { name: "毕昇", title: "活字印刷", stats: { command: 30, martial: 35, wisdom: 88, politics: 55, charisma: 65, craft: 96 } }
    ],
    adj: ["henan", "anhui", "jiangxi", "hunan", "chongqing", "shaanxi"]
  },

  // 安徽 - 江淮之间，帝王之乡
  anhui: {
    name: "安徽",
    color: "#d35400",
    heroes: [
      { name: "朱元璋", title: "明太祖", stats: { command: 94, martial: 80, wisdom: 90, politics: 96, charisma: 88, craft: 55 } },
      { name: "曹操", title: "魏武帝", stats: { command: 96, martial: 72, wisdom: 94, politics: 92, charisma: 88, craft: 85 } },
      { name: "周瑜", title: "美周郎", stats: { command: 92, martial: 75, wisdom: 90, politics: 78, charisma: 95, craft: 82 } },
      { name: "华佗", title: "神医", stats: { command: 35, martial: 40, wisdom: 95, politics: 50, charisma: 85, craft: 98 } },
      { name: "包拯", title: "包青天", stats: { command: 55, martial: 50, wisdom: 88, politics: 95, charisma: 90, craft: 60 } },
      { name: "李鸿章", title: "晚清重臣", stats: { command: 70, martial: 55, wisdom: 88, politics: 90, charisma: 75, craft: 72 } }
    ],
    adj: ["jiangsu", "zhejiang", "jiangxi", "henan", "hubei"]
  },

  // 四川 - 天府之国，蜀汉基业
  sichuan: {
    name: "四川",
    color: "#9b59b6",
    heroes: [
      { name: "诸葛亮", title: "武侯", stats: { command: 92, martial: 45, wisdom: 98, politics: 96, charisma: 95, craft: 88 } },
      { name: "李白", title: "诗仙", stats: { command: 45, martial: 55, wisdom: 88, politics: 40, charisma: 98, craft: 96 } },
      { name: "苏轼", title: "东坡居士", stats: { command: 55, martial: 50, wisdom: 92, politics: 85, charisma: 95, craft: 94 } },
      { name: "张飞", title: "万人敌", stats: { command: 88, martial: 96, wisdom: 45, politics: 35, charisma: 80, craft: 55 } },
      { name: "武则天", title: "则天皇帝", stats: { command: 82, martial: 50, wisdom: 92, politics: 98, charisma: 88, craft: 70 } },
      { name: "司马相如", title: "赋圣", stats: { command: 40, martial: 45, wisdom: 88, politics: 65, charisma: 85, craft: 95 } }
    ],
    adj: ["shaanxi", "gansu", "chongqing", "guizhou", "yunnan", "qinghai"]
  },

  // 河北 - 燕赵大地，慷慨悲歌
  hebei: {
    name: "河北",
    color: "#8e44ad",
    heroes: [
      { name: "刘备", title: "昭烈帝", stats: { command: 82, martial: 72, wisdom: 85, politics: 88, charisma: 98, craft: 60 } },
      { name: "赵云", title: "常山赵子龙", stats: { command: 90, martial: 96, wisdom: 78, politics: 65, charisma: 92, craft: 58 } },
      { name: "张飞", title: "万人敌", stats: { command: 88, martial: 96, wisdom: 45, politics: 35, charisma: 80, craft: 55 } },
      { name: "赵匡胤", title: "宋太祖", stats: { command: 92, martial: 88, wisdom: 88, politics: 95, charisma: 90, craft: 65 } },
      { name: "祖冲之", title: "数学巨匠", stats: { command: 35, martial: 30, wisdom: 96, politics: 55, charisma: 70, craft: 98 } },
      { name: "扁鹊", title: "医祖", stats: { command: 40, martial: 45, wisdom: 95, politics: 60, charisma: 82, craft: 96 } }
    ],
    adj: ["beijing", "tianjin", "shanxi", "henan", "shandong"]
  },

  // ==================== 二档省份（3-4人）====================

  // 山西 - 三晋大地，表里山河
  shanxi: {
    name: "山西",
    color: "#16a085",
    heroes: [
      { name: "关羽", title: "武圣", stats: { command: 92, martial: 98, wisdom: 75, politics: 60, charisma: 96, craft: 55 } },
      { name: "卫青", title: "大将军", stats: { command: 96, martial: 85, wisdom: 82, politics: 70, charisma: 85, craft: 50 } },
      { name: "霍去病", title: "冠军侯", stats: { command: 95, martial: 92, wisdom: 75, politics: 45, charisma: 88, craft: 48 } },
      { name: "狄仁杰", title: "神探", stats: { command: 65, martial: 55, wisdom: 95, politics: 92, charisma: 88, craft: 70 } }
    ],
    adj: ["hebei", "neimenggu", "shaanxi", "henan"]
  },

  // 甘肃 - 河西走廊，丝路重镇
  gansu: {
    name: "甘肃",
    color: "#27ae60",
    heroes: [
      { name: "李广", title: "飞将军", stats: { command: 90, martial: 92, wisdom: 70, politics: 35, charisma: 90, craft: 55 } },
      { name: "赵充国", title: "屯田名将", stats: { command: 88, martial: 82, wisdom: 88, politics: 75, charisma: 78, craft: 65 } },
      { name: "皇甫谧", title: "针灸鼻祖", stats: { command: 35, martial: 40, wisdom: 92, politics: 55, charisma: 75, craft: 95 } }
    ],
    adj: ["shaanxi", "sichuan", "qinghai", "xinjiang", "neimenggu", "ningxia"]
  },

  // 湖南 - 潇湘之地，惟楚有才
  hunan: {
    name: "湖南",
    color: "#f39c12",
    heroes: [
      { name: "曾国藩", title: "晚清中兴", stats: { command: 88, martial: 65, wisdom: 90, politics: 92, charisma: 85, craft: 75 } },
      { name: "左宗棠", title: "收复新疆", stats: { command: 90, martial: 75, wisdom: 88, politics: 88, charisma: 86, craft: 70 } },
      { name: "蔡伦", title: "造纸术", stats: { command: 40, martial: 35, wisdom: 88, politics: 70, charisma: 72, craft: 98 } },
      { name: "王夫之", title: "船山先生", stats: { command: 45, martial: 40, wisdom: 95, politics: 65, charisma: 75, craft: 88 } }
    ],
    adj: ["hubei", "jiangxi", "guangdong", "guangxi", "guizhou"]
  },

  // 江西 - 物华天宝，人杰地灵
  jiangxi: {
    name: "江西",
    color: "#f1c40f",
    heroes: [
      { name: "陶渊明", title: "田园诗人", stats: { command: 35, martial: 40, wisdom: 90, politics: 55, charisma: 88, craft: 92 } },
      { name: "王安石", title: "变法名相", stats: { command: 70, martial: 50, wisdom: 92, politics: 95, charisma: 75, craft: 82 } },
      { name: "文天祥", title: "忠烈千秋", stats: { command: 82, martial: 75, wisdom: 88, politics: 80, charisma: 96, craft: 78 } },
      { name: "黄庭坚", title: "书法大家", stats: { command: 45, martial: 40, wisdom: 88, politics: 65, charisma: 78, craft: 94 } }
    ],
    adj: ["anhui", "zhejiang", "fujian", "guangdong", "hunan", "hubei"]
  },

  // 福建 - 八闽大地，海上丝路
  fujian: {
    name: "福建",
    color: "#2ecc71",
    heroes: [
      { name: "郑成功", title: "国姓爷", stats: { command: 92, martial: 88, wisdom: 85, politics: 82, charisma: 94, craft: 75 } },
      { name: "林则徐", title: "民族英雄", stats: { command: 75, martial: 60, wisdom: 90, politics: 92, charisma: 92, craft: 70 } },
      { name: "朱熹", title: "理学大师", stats: { command: 40, martial: 35, wisdom: 98, politics: 85, charisma: 88, craft: 85 } },
      { name: "严复", title: "启蒙思想家", stats: { command: 45, martial: 40, wisdom: 92, politics: 78, charisma: 80, craft: 88 } }
    ],
    adj: ["zhejiang", "jiangxi", "guangdong", "taiwan"]
  },

  // 广东 - 岭南之地，开放前沿
  guangdong: {
    name: "广东",
    color: "#e74c3c",
    heroes: [
      { name: "孙中山", title: "国父", stats: { command: 75, martial: 55, wisdom: 92, politics: 95, charisma: 98, craft: 70 } },
      { name: "六祖慧能", title: "禅宗六祖", stats: { command: 40, martial: 35, wisdom: 98, politics: 60, charisma: 95, craft: 85 } },
      { name: "袁崇焕", title: "督师", stats: { command: 88, martial: 82, wisdom: 80, politics: 65, charisma: 85, craft: 60 } },
      { name: "康有为", title: "维新领袖", stats: { command: 50, martial: 40, wisdom: 88, politics: 88, charisma: 85, craft: 75 } }
    ],
    adj: ["fujian", "jiangxi", "hunan", "guangxi", "hainan"]
  },

  // 辽宁 - 关外重镇，满清发源
  liaoning: {
    name: "辽宁",
    color: "#3498db",
    heroes: [
      { name: "努尔哈赤", title: "清太祖", stats: { command: 95, martial: 90, wisdom: 88, politics: 92, charisma: 90, craft: 65 } },
      { name: "皇太极", title: "清太宗", stats: { command: 92, martial: 85, wisdom: 90, politics: 95, charisma: 88, craft: 70 } },
      { name: "李光弼", title: "中兴名将", stats: { command: 90, martial: 82, wisdom: 85, politics: 75, charisma: 82, craft: 55 } }
    ],
    adj: ["jilin", "neimenggu", "hebei"]
  },

  // 内蒙古 - 草原帝国，天骄故里
  neimenggu: {
    name: "内蒙古",
    color: "#1abc9c",
    heroes: [
      { name: "成吉思汗", title: "一代天骄", stats: { command: 100, martial: 95, wisdom: 92, politics: 95, charisma: 98, craft: 70 } },
      { name: "忽必烈", title: "元世祖", stats: { command: 92, martial: 82, wisdom: 90, politics: 94, charisma: 88, craft: 75 } },
      { name: "耶律楚材", title: "契丹名相", stats: { command: 65, martial: 55, wisdom: 95, politics: 95, charisma: 85, craft: 80 } },
      { name: "吕布", title: "飞将", stats: { command: 82, martial: 98, wisdom: 45, politics: 25, charisma: 70, craft: 60 } }
    ],
    adj: ["shanxi", "heilongjiang", "jilin", "liaoning", "gansu", "ningxia"]
  },

  // 北京 - 天子脚下，首善之区
  beijing: {
    name: "北京",
    color: "#c0392b",
    heroes: [
      { name: "于谦", title: "救时宰相", stats: { command: 88, martial: 72, wisdom: 92, politics: 95, charisma: 90, craft: 65 } },
      { name: "纳兰性德", title: "满清第一词人", stats: { command: 55, martial: 60, wisdom: 88, politics: 65, charisma: 85, craft: 94 } },
      { name: "刘墉", title: "浓墨宰相", stats: { command: 60, martial: 50, wisdom: 88, politics: 88, charisma: 82, craft: 90 } }
    ],
    adj: ["hebei", "tianjin"]
  },

  // 云南 - 彩云之南，民族融合
  yunnan: {
    name: "云南",
    color: "#9b59b6",
    heroes: [
      { name: "郑和", title: "三宝太监", stats: { command: 95, martial: 78, wisdom: 90, politics: 85, charisma: 92, craft: 88 } },
      { name: "段思平", title: "大理开国", stats: { command: 85, martial: 82, wisdom: 88, politics: 82, charisma: 85, craft: 70 } },
      { name: "兰茂", title: "滇南本草", stats: { command: 40, martial: 45, wisdom: 90, politics: 60, charisma: 75, craft: 92 } },
      { name: "杨慎", title: "明代才子", stats: { command: 50, martial: 45, wisdom: 92, politics: 75, charisma: 82, craft: 90 } }
    ],
    adj: ["sichuan", "guizhou", "guangxi", "xizang"]
  },

  // ==================== 三档省份（2-3人）====================

  // 天津 - 九河下梢，京师门户
  tianjin: {
    name: "天津",
    color: "#2980b9",
    heroes: [
      { name: "戚继光", title: "抗倭名将", stats: { command: 95, martial: 90, wisdom: 88, politics: 75, charisma: 90, craft: 85 } },
      { name: "霍元甲", title: "精武英雄", stats: { command: 70, martial: 95, wisdom: 75, politics: 50, charisma: 88, craft: 82 } }
    ],
    adj: ["hebei", "beijing"]
  },

  // 上海 - 东方明珠，十里洋场
  shanghai: {
    name: "上海",
    color: "#e67e22",
    heroes: [
      { name: "徐光启", title: "科学先驱", stats: { command: 55, martial: 45, wisdom: 92, politics: 82, charisma: 80, craft: 95 } },
      { name: "黄道婆", title: "纺织鼻祖", stats: { command: 40, martial: 35, wisdom: 85, politics: 55, charisma: 82, craft: 96 } }
    ],
    adj: ["jiangsu", "zhejiang"]
  },

  // 重庆 - 山城雾都，巴渝故地
  chongqing: {
    name: "重庆",
    color: "#d35400",
    heroes: [
      { name: "秦良玉", title: "巾帼英雄", stats: { command: 88, martial: 85, wisdom: 82, politics: 75, charisma: 88, craft: 60 } },
      { name: "刘伯承", title: "军神", stats: { command: 95, martial: 78, wisdom: 90, politics: 85, charisma: 88, craft: 70 } }
    ],
    adj: ["sichuan", "hubei", "hunan", "guizhou"]
  },

  // 贵州 - 黔中大地，夜郎故国
  guizhou: {
    name: "贵州",
    color: "#16a085",
    heroes: [
      { name: "王阳明", title: "龙场悟道", stats: { command: 78, martial: 68, wisdom: 98, politics: 85, charisma: 92, craft: 88 } },
      { name: "张之洞", title: "洋务领袖", stats: { command: 65, martial: 55, wisdom: 90, politics: 92, charisma: 85, craft: 82 } }
    ],
    adj: ["sichuan", "chongqing", "hunan", "guangxi", "yunnan"]
  },

  // 广西 - 八桂大地，岭南要地
  guangxi: {
    name: "广西",
    color: "#27ae60",
    heroes: [
      { name: "冯子材", title: "镇南关大捷", stats: { command: 88, martial: 85, wisdom: 80, politics: 70, charisma: 86, craft: 60 } },
      { name: "石达开", title: "翼王", stats: { command: 90, martial: 82, wisdom: 88, politics: 75, charisma: 92, craft: 68 } }
    ],
    adj: ["guangdong", "hunan", "guizhou", "yunnan"]
  },

  // 海南 - 天涯海角，南海明珠
  hainan: {
    name: "海南",
    color: "#f39c12",
    heroes: [
      { name: "海瑞", title: "清官典范", stats: { command: 60, martial: 55, wisdom: 88, politics: 92, charisma: 88, craft: 65 } },
      { name: "丘濬", title: "理学名臣", stats: { command: 55, martial: 45, wisdom: 90, politics: 88, charisma: 80, craft: 78 } }
    ],
    adj: ["guangdong"]
  },

  // 台湾 - 宝岛台湾，祖国明珠
  taiwan: {
    name: "台湾",
    color: "#1abc9c",
    heroes: [
      { name: "郑成功", title: "延平郡王", stats: { command: 92, martial: 88, wisdom: 85, politics: 82, charisma: 94, craft: 75 } },
      { name: "刘铭传", title: "台湾巡抚", stats: { command: 82, martial: 75, wisdom: 88, politics: 90, charisma: 85, craft: 78 } }
    ],
    adj: ["fujian"]
  },

  // 香港 - 东方之珠
  hongkong: {
    name: "香港",
    color: "#e74c3c",
    heroes: [
      { name: "何东", title: "香港首富", stats: { command: 65, martial: 40, wisdom: 88, politics: 75, charisma: 88, craft: 82 } }
    ],
    adj: ["guangdong"]
  },

  // 澳门 - 濠江明珠
  macau: {
    name: "澳门",
    color: "#3498db",
    heroes: [
      { name: "郑观应", title: "维新思想家", stats: { command: 50, martial: 40, wisdom: 90, politics: 82, charisma: 80, craft: 85 } }
    ],
    adj: ["guangdong"]
  },

  // 吉林 - 白山黑水
  jilin: {
    name: "吉林",
    color: "#9b59b6",
    heroes: [
      { name: "鳌拜", title: "满洲第一勇士", stats: { command: 85, martial: 95, wisdom: 55, politics: 70, charisma: 75, craft: 50 } },
      { name: "宋小濂", title: "吉林知府", stats: { command: 60, martial: 50, wisdom: 85, politics: 82, charisma: 78, craft: 70 } }
    ],
    adj: ["heilongjiang", "liaoning", "neimenggu"]
  },

  // 黑龙江 - 北国粮仓
  heilongjiang: {
    name: "黑龙江",
    color: "#2ecc71",
    heroes: [
      { name: "完颜阿骨打", title: "金太祖", stats: { command: 92, martial: 90, wisdom: 85, politics: 88, charisma: 90, craft: 60 } },
      { name: "李金镛", title: "漠河金矿", stats: { command: 70, martial: 60, wisdom: 85, politics: 78, charisma: 82, craft: 75 } }
    ],
    adj: ["jilin", "neimenggu"]
  },

  // 青海 - 三江之源
  qinghai: {
    name: "青海",
    color: "#f1c40f",
    heroes: [
      { name: "无恤", title: "吐谷浑名将", stats: { command: 82, martial: 78, wisdom: 75, politics: 65, charisma: 78, craft: 55 } },
      { name: "宗喀巴", title: "格鲁派创始人", stats: { command: 50, martial: 40, wisdom: 95, politics: 85, charisma: 92, craft: 80 } }
    ],
    adj: ["gansu", "sichuan", "xinjiang", "xizang"]
  },

  // 宁夏 - 塞上江南
  ningxia: {
    name: "宁夏",
    color: "#e67e22",
    heroes: [
      { name: "李元昊", title: "西夏景宗", stats: { command: 90, martial: 85, wisdom: 88, politics: 85, charisma: 88, craft: 70 } },
      { name: "韩世忠", title: "中兴名将", stats: { command: 92, martial: 90, wisdom: 82, politics: 75, charisma: 88, craft: 62 } }
    ],
    adj: ["shaanxi", "gansu", "neimenggu"]
  },

  // 新疆 - 西域明珠
  xinjiang: {
    name: "新疆",
    color: "#d35400",
    heroes: [
      { name: "班超", title: "西域都护", stats: { command: 92, martial: 85, wisdom: 90, politics: 88, charisma: 92, craft: 65 } },
      { name: "鸠摩罗什", title: "译经大师", stats: { command: 45, martial: 40, wisdom: 98, politics: 75, charisma: 95, craft: 90 } }
    ],
    adj: ["gansu", "qinghai", "xizang"]
  },

  // 西藏 - 雪域高原
  xizang: {
    name: "西藏",
    color: "#8e44ad",
    heroes: [
      { name: "松赞干布", title: "吐蕃赞普", stats: { command: 88, martial: 85, wisdom: 88, politics: 92, charisma: 90, craft: 75 } },
      { name: "八思巴", title: "国师", stats: { command: 60, martial: 50, wisdom: 95, politics: 90, charisma: 92, craft: 88 } }
    ],
    adj: ["yunnan", "sichuan", "qinghai", "xinjiang"]
  }
};

// 省份GeoJSON名称映射
const geoNameMap = {
  "北京": "beijing",
  "天津": "tianjin",
  "河北": "hebei",
  "山西": "shanxi",
  "内蒙古": "neimenggu",
  "辽宁": "liaoning",
  "吉林": "jilin",
  "黑龙江": "heilongjiang",
  "上海": "shanghai",
  "江苏": "jiangsu",
  "浙江": "zhejiang",
  "安徽": "anhui",
  "福建": "fujian",
  "江西": "jiangxi",
  "山东": "shandong",
  "河南": "henan",
  "湖北": "hubei",
  "湖南": "hunan",
  "广东": "guangdong",
  "广西": "guangxi",
  "海南": "hainan",
  "重庆": "chongqing",
  "四川": "sichuan",
  "贵州": "guizhou",
  "云南": "yunnan",
  "西藏": "xizang",
  "陕西": "shaanxi",
  "甘肃": "gansu",
  "青海": "qinghai",
  "宁夏": "ningxia",
  "新疆": "xinjiang",
  "台湾": "taiwan",
  "香港": "hongkong",
  "澳门": "macau"
};

// 导出数据（兼容不同模块系统）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { provinceData, geoNameMap };
}
