// ========================================
// 详细能力数据模型
// ========================================
const figureDetailModel = {
  abilities: {
    political: { name: "政治", desc: "治国理政、政治谋略" },
    military: { name: "军事", desc: "用兵、战略、战术" },
    literary: { name: "文学", desc: "诗词文章、文学创作" },
    artistic: { name: "艺术", desc: "绘画、音乐、书法等" },
    strategic: { name: "战略", desc: "长远规划、大局观" },
    charisma: { name: "魅力", desc: "人格魅力、感染力" },
    innovation: { name: "创新", desc: "思想创新、改革魄力" },
    leadership: { name: "领导", desc: "团队管理、组织能力" }
  }
};

// ========================================
// 省份代表人物数据
// ========================================
const provinceData = {
  // 华北地区
  beijing: {
    name: "北京",
    hero: "于谦",
    title: "北京保卫战统帅",
    type: "文臣",
    power: 85,
    conquered: false,
    adj: ["hebei", "tianjin"]
  },
  tianjin: {
    name: "天津",
    hero: "戚继光",
    title: "抗倭名将",
    type: "名将",
    power: 92,
    conquered: false,
    adj: ["hebei", "beijing"]
  },
  hebei: {
    name: "河北",
    hero: "赵云",
    title: "常山赵子龙",
    type: "名将",
    power: 95,
    conquered: false,
    adj: ["beijing", "tianjin", "shanxi", "henan", "shandong"]
  },
  shanxi: {
    name: "山西",
    hero: "卫青",
    title: "大将军",
    type: "名将",
    power: 97,
    conquered: false,
    adj: ["hebei", "neimenggu", "shaanxi", "henan"]
  },
  neimenggu: {
    name: "内蒙古",
    hero: "成吉思汗",
    title: "蒙古帝国创建者",
    type: "君主",
    power: 99,
    conquered: false,
    adj: ["shanxi", "heilongjiang", "jilin", "liaoning", "gansu", "ningxia"]
  },

  // 东北地区
  liaoning: {
    name: "辽宁",
    hero: "多尔衮",
    title: "清初摄政王",
    type: "名将",
    power: 90,
    conquered: false,
    adj: ["jilin", "neimenggu", "hebei"]
  },
  jilin: {
    name: "吉林",
    hero: "鳌拜",
    title: "满洲第一巴图鲁",
    type: "名将",
    power: 85,
    conquered: false,
    adj: ["heilongjiang", "liaoning", "neimenggu"]
  },
  heilongjiang: {
    name: "黑龙江",
    hero: "完颜阿骨打",
    title: "金国开国皇帝",
    type: "君主",
    power: 95,
    conquered: false,
    adj: ["jilin", "neimenggu"]
  },

  // 华东地区
  shanghai: {
    name: "上海",
    hero: "徐光启",
    title: "明末科学家",
    type: "文臣",
    power: 75,
    conquered: false,
    adj: ["jiangsu", "zhejiang"]
  },
  jiangsu: {
    name: "江苏",
    hero: "韩信",
    title: "兵仙",
    type: "名将",
    power: 98,
    conquered: false,
    adj: ["shanghai", "zhejiang", "anhui", "shandong"]
  },
  zhejiang: {
    name: "浙江",
    hero: "岳飞",
    title: "精忠报国",
    type: "名将",
    power: 98,
    conquered: false,
    adj: ["shanghai", "jiangsu", "anhui", "jiangxi", "fujian"]
  },
  anhui: {
    name: "安徽",
    hero: "朱元璋",
    title: "明朝开国皇帝",
    type: "君主",
    power: 96,
    conquered: false,
    adj: ["jiangsu", "zhejiang", "jiangxi", "henan", "hubei"]
  },
  fujian: {
    name: "福建",
    hero: "郑成功",
    title: "国姓爷",
    type: "名将",
    power: 92,
    conquered: false,
    adj: ["zhejiang", "jiangxi", "guangdong", "taiwan"]
  },
  jiangxi: {
    name: "江西",
    hero: "文天祥",
    title: "忠烈千秋",
    type: "文臣",
    power: 88,
    conquered: false,
    adj: ["anhui", "zhejiang", "fujian", "guangdong", "hunan", "hubei"]
  },
  shandong: {
    name: "山东",
    hero: "孙武",
    title: "兵圣",
    type: "谋士",
    power: 95,
    conquered: false,
    adj: ["hebei", "henan", "jiangsu"]
  },
  taiwan: {
    name: "台湾",
    hero: "郑经",
    title: "延平郡王",
    type: "名将",
    power: 75,
    conquered: false,
    adj: ["fujian"]
  },

  // 华中地区
  henan: {
    name: "河南",
    hero: "诸葛亮",
    title: "卧龙先生",
    type: "谋士",
    power: 97,
    conquered: false,
    adj: ["shanxi", "hebei", "shandong", "anhui", "hubei", "shaanxi"]
  },
  hubei: {
    name: "湖北",
    hero: "伍子胥",
    title: "复仇之神",
    type: "名将",
    power: 88,
    conquered: false,
    adj: ["henan", "anhui", "jiangxi", "hunan", "chongqing", "shaanxi"]
  },
  hunan: {
    name: "湖南",
    hero: "曾国藩",
    title: "湘军创始人",
    type: "文臣",
    power: 90,
    conquered: false,
    adj: ["hubei", "jiangxi", "guangdong", "guangxi", "guizhou"]
  },

  // 华南地区
  guangdong: {
    name: "广东",
    hero: "袁崇焕",
    title: "蓟辽督师",
    type: "名将",
    power: 88,
    conquered: false,
    adj: ["fujian", "jiangxi", "hunan", "guangxi", "hainan"]
  },
  guangxi: {
    name: "广西",
    hero: "冯子材",
    title: "镇南关大捷",
    type: "名将",
    power: 85,
    conquered: false,
    adj: ["guangdong", "hunan", "guizhou", "yunnan"]
  },
  hainan: {
    name: "海南",
    hero: "海瑞",
    title: "清官典范",
    type: "文臣",
    power: 75,
    conquered: false,
    adj: ["guangdong"]
  },
  hongkong: {
    name: "香港",
    hero: "无名",
    title: "商业之城",
    type: "无",
    power: 50,
    conquered: false,
    adj: ["guangdong"]
  },
  macau: {
    name: "澳门",
    hero: "无名",
    title: "商业之城",
    type: "无",
    power: 50,
    conquered: false,
    adj: ["guangdong"]
  },

  // 西南地区
  sichuan: {
    name: "四川",
    hero: "张飞",
    title: "万人敌",
    type: "名将",
    power: 93,
    conquered: false,
    adj: ["shaanxi", "gansu", "chongqing", "guizhou", "yunnan", "qinghai"]
  },
  chongqing: {
    name: "重庆",
    hero: "秦良玉",
    title: "巾帼英雄",
    type: "名将",
    power: 85,
    conquered: false,
    adj: ["sichuan", "hubei", "hunan", "guizhou"]
  },
  guizhou: {
    name: "贵州",
    hero: "王阳明",
    title: "心学大师",
    type: "文臣",
    power: 88,
    conquered: false,
    adj: ["sichuan", "chongqing", "hunan", "guangxi", "yunnan"]
  },
  yunnan: {
    name: "云南",
    hero: "沐英",
    title: "镇守云南",
    type: "名将",
    power: 85,
    conquered: false,
    adj: ["sichuan", "guizhou", "guangxi", "xizang"]
  },
  xizang: {
    name: "西藏",
    hero: "松赞干布",
    title: "吐蕃赞普",
    type: "君主",
    power: 85,
    conquered: false,
    adj: ["yunnan", "sichuan", "qinghai", "xinjiang"]
  },

  // 西北地区
  shaanxi: {
    name: "陕西",
    hero: "秦始皇",
    title: "千古一帝",
    type: "君主",
    power: 100,
    conquered: true, // 起始省份
    adj: ["shanxi", "henan", "hubei", "sichuan", "gansu", "ningxia", "neimenggu"]
  },
  gansu: {
    name: "甘肃",
    hero: "李广",
    title: "飞将军",
    type: "名将",
    power: 90,
    conquered: false,
    adj: ["shaanxi", "sichuan", "qinghai", "xinjiang", "neimenggu", "ningxia"]
  },
  qinghai: {
    name: "青海",
    hero: "无恤",
    title: "吐谷浑名将",
    type: "名将",
    power: 75,
    conquered: false,
    adj: ["gansu", "sichuan", "xinjiang", "xizang"]
  },
  ningxia: {
    name: "宁夏",
    hero: "李元昊",
    title: "西夏开国皇帝",
    type: "君主",
    power: 85,
    conquered: false,
    adj: ["shaanxi", "gansu", "neimenggu"]
  },
  xinjiang: {
    name: "新疆",
    hero: "班超",
    title: "西域都护",
    type: "名将",
    power: 92,
    conquered: false,
    adj: ["gansu", "qinghai", "xizang"]
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

// 征服阶段定义
const conquestStages = [
  {
    name: "西北统一",
    path: ["gansu", "ningxia", "qinghai", "xinjiang"]
  },
  {
    name: "南下蜀地",
    path: ["sichuan", "chongqing"]
  },
  {
    name: "西南平定",
    path: ["yunnan", "guizhou", "guangxi", "xizang"]
  },
  {
    name: "华南进取",
    path: ["guangdong", "hainan", "hongkong", "macau"]
  },
  {
    name: "东进中原",
    path: ["henan", "hubei", "hunan"]
  },
  {
    name: "东南一统",
    path: ["jiangxi", "fujian", "taiwan"]
  },
  {
    name: "江淮之战",
    path: ["anhui", "jiangsu", "zhejiang", "shanghai"]
  },
  {
    name: "齐鲁兼并",
    path: ["shandong"]
  },
  {
    name: "燕赵之战",
    path: ["shanxi", "hebei", "beijing", "tianjin"]
  },
  {
    name: "关外征伐",
    path: ["neimenggu", "liaoning", "jilin", "heilongjiang"]
  }
];

// ========================================
// 人物详细数据（扩展字段）
// ========================================
const figureDetails = {
  // ===== 西北地区 =====
  shaanxi: {
    fullName: "嬴政",
    era: "秦朝",
    dynasty: "秦",
    birthYear: -259,
    deathYear: -210,
    birthPlace: "邯郸（今河北邯郸）",
    
    biography: {
      summary: "中国历史上第一位皇帝，统一六国，建立中央集权制度，开创大一统格局。",
      keyEvents: [
        { year: -247, age: 13, event: "继承秦王位", significance: "开始了漫长的统治生涯" },
        { year: -238, age: 22, event: "亲政，铲除吕不韦势力", significance: "开始独立执政" },
        { year: -221, age: 39, event: "统一六国", significance: "中国历史上首次大一统" },
        { year: -213, age: 47, event: "焚书坑儒", significance: "思想统一的极端措施" },
        { year: -210, age: 50, event: "病逝于沙丘", significance: "一代帝王陨落" }
      ]
    },
    
    abilities: {
      political: { score: 99, desc: "开创中央集权，统一六国" },
      military: { score: 88, desc: "善用名将，统一天下" },
      literary: { score: 45, desc: "焚书坑儒，文化暴君" },
      artistic: { score: 60, desc: "建筑宏伟，阿房宫、兵马俑" },
      strategic: { score: 98, desc: "远交近攻，各个击破" },
      charisma: { score: 75, desc: "威严霸气，令人敬畏" },
      innovation: { score: 95, desc: "书同文、车同轨" },
      leadership: { score: 98, desc: "驾驭群臣，号令天下" }
    },
    
    achievements: [
      { title: "统一六国", year: -221, impact: 10, desc: "中国历史上首次大一统" },
      { title: "创建皇帝制度", year: -221, impact: 10, desc: "开创中央集权制度，影响两千年" },
      { title: "修建万里长城", year: -214, impact: 9, desc: "世界七大奇迹之一" }
    ],
    
    story: "【千古一帝】\n\n公元前259年，一个婴儿在赵国邯郸诞生。他叫嬴政，是秦国派驻赵国的人质的儿子。\n\n没有人能想到，这个在异国他乡艰难求生的孩子，日后会成为统一中国的第一位皇帝。\n\n13岁继承王位，22岁铲除权臣吕不韦，30岁开始了长达十年的统一战争。他任用王翦、蒙恬等名将，采用远交近攻的策略，先后灭掉韩、赵、魏、楚、燕、齐六国。\n\n公元前221年，39岁的嬴政完成了中国历史上第一次大一统。他自称"始皇帝"，建立中央集权制度，统一文字、货币、度量衡，修建万里长城。"
  },

  gansu: {
    fullName: "李广",
    era: "西汉",
    dynasty: "汉",
    birthYear: -183,
    deathYear: -119,
    birthPlace: "陇西成纪（今甘肃天水）",
    
    biography: {
      summary: "西汉名将，匈奴人闻风丧胆的'飞将军'，一生征战匈奴七十余次。",
      keyEvents: [
        { year: -166, age: 17, event: "从军击胡", significance: "开启军旅生涯" },
        { year: -144, age: 39, event: "任上郡太守", significance: "飞将军威名远播" },
        { year: -119, age: 64, event: "迷路自尽", significance: "一代名将的悲剧结局" }
      ]
    },
    
    abilities: {
      political: { score: 35, desc: "不善官场，未能封侯" },
      military: { score: 96, desc: "骑兵战术大师，箭术出神入化" },
      literary: { score: 40, desc: "粗通文墨" },
      artistic: { score: 30, desc: "无特别记载" },
      strategic: { score: 78, desc: "战术灵活，善于机动" },
      charisma: { score: 92, desc: "士兵爱戴，匈奴敬畏" },
      innovation: { score: 70, desc: "骑射战术创新" },
      leadership: { score: 88, desc: "身先士卒，爱兵如子" }
    },
    
    achievements: [
      { title: "匈奴称飞将军", year: -144, impact: 9, desc: "匈奴数年不敢犯境" },
      { title: "箭术天下无双", year: -150, impact: 8, desc: "射石没羽" },
      { title: "一生征战七十余次", year: -119, impact: 8, desc: "汉朝边疆守护者" }
    ],
    
    story: "【飞将军的传说】\n\n\"但使龙城飞将在，不教胡马度阴山。\"\n\n李广，一个让匈奴闻风丧胆的名字。\n\n他箭术通神，传说能射箭入石。一次打猎时，他误将石头当作老虎，一箭射去，箭矢没入石中。\n\n他身经七十余战，从无败绩，却始终未能封侯。\n\n匈奴人称他为\"飞将军\"，数年不敢进犯他镇守的边境。\n\n\"李广难封\"，成为千古遗憾。"
  },

  henan: {
    fullName: "诸葛亮",
    era: "三国",
    dynasty: "蜀汉",
    birthYear: 181,
    deathYear: 234,
    birthPlace: "琅琊阳都（今山东沂南）",
    
    biography: {
      summary: "三国时期蜀汉丞相，杰出的政治家、军事家，鞠躬尽瘁，死而后已。",
      keyEvents: [
        { year: 207, age: 26, event: "三顾茅庐", significance: "出山辅佐刘备" },
        { year: 208, age: 27, event: "赤壁之战", significance: "联吴抗曹" },
        { year: 221, age: 40, event: "蜀汉建立", significance: "任丞相" },
        { year: 227, age: 46, event: "北伐中原", significance: "出师表" },
        { year: 234, age: 53, event: "五丈原病逝", significance: "鞠躬尽瘁" }
      ]
    },
    
    abilities: {
      political: { score: 98, desc: "治蜀有方，法制严明" },
      military: { score: 92, desc: "六出祁山，虽未成功但战略正确" },
      literary: { score: 95, desc: "出师表，千古名篇" },
      artistic: { score: 70, desc: "精通音律" },
      strategic: { score: 99, desc: "隆中对，三分天下" },
      charisma: { score: 98, desc: "万世敬仰，忠臣楷模" },
      innovation: { score: 88, desc: "木牛流马，诸葛连弩" },
      leadership: { score: 96, desc: "鞠躬尽瘁，死而后已" }
    },
    
    achievements: [
      { title: "隆中对", year: 207, impact: 9, desc: "三分天下的战略构想" },
      { title: "赤壁之战", year: 208, impact: 10, desc: "联吴抗曹，奠定三国格局" },
      { title: "治蜀", year: 221, impact: 9, desc: "法治严明，蜀中大治" },
      { title: "出师表", year: 227, impact: 10, desc: "千古忠臣名篇" }
    ],
    
    story: "【卧龙出山】\n\n隆中草庐，一个书生正在等待。\n\n他说：\"苟全性命于乱世，不求闻达于诸侯。\"\n\n刘备三顾茅庐，终于请出这位隐居的天才。\n\n他叫诸葛亮，字孔明，号卧龙。\n\n赤壁之战，他联吴抗曹；入川之战，他运筹帷幄；白帝托孤，他鞠躬尽瘁。\n\n六出祁山，五丈原上，他与司马懿对峙。他知道天命难违，但依然\"知其不可而为之\"。\n\n234年，诸葛亮病逝于五丈原。\n\n\"鞠躬尽瘁，死而后已。\"这八个字，成为千古忠臣的写照。"
  },

  zhejiang: {
    fullName: "岳飞",
    era: "南宋",
    dynasty: "宋",
    birthYear: 1103,
    deathYear: 1142,
    birthPlace: "相州汤阴（今河南汤阴）",
    
    biography: {
      summary: "南宋抗金名将，精忠报国，岳家军威震天下，却被秦桧以莫须有罪名杀害。",
      keyEvents: [
        { year: 1122, age: 19, event: "投身军旅", significance: "刺字精忠报国" },
        { year: 1129, age: 26, event: "创建岳家军", significance: "纪律严明" },
        { year: 1134, age: 31, event: "收复襄阳六郡", significance: "首次北伐成功" },
        { year: 1140, age: 37, event: "郾城大捷", significance: "击败金军主力" },
        { year: 1142, age: 39, event: "风波亭遇害", significance: "莫须有罪名" }
      ]
    },
    
    abilities: {
      political: { score: 50, desc: "不谙政治，遭奸臣陷害" },
      military: { score: 99, desc: "百战百胜，用兵如神" },
      literary: { score: 85, desc: "满江红，气壮山河" },
      artistic: { score: 60, desc: "书法苍劲有力" },
      strategic: { score: 92, desc: "连结河朔，收复中原" },
      charisma: { score: 98, desc: "精忠报国，万世敬仰" },
      innovation: { score: 85, desc: "岳家军战法独特" },
      leadership: { score: 98, desc: "冻死不拆屋，饿死不掳掠" }
    },
    
    achievements: [
      { title: "创建岳家军", year: 1129, impact: 9, desc: "纪律严明，秋毫无犯" },
      { title: "收复襄阳六郡", year: 1134, impact: 8, desc: "南宋首次大举反攻" },
      { title: "郾城大捷", year: 1140, impact: 10, desc: "击败金军主力骑兵" },
      { title: "满江红", year: 1136, impact: 9, desc: "千古名篇，气壮山河" }
    ],
    
    story: "【精忠报国】\n\n他出生时，黄河决堤。母亲抱着他在大缸中漂流，得以幸存。\n\n他叫岳飞，从小便有报国之志。母亲在他背上刺下四个字：精忠报国。\n\n他创建了岳家军，纪律严明：\"冻死不拆屋，饿死不掳掠。\"\n\n金人闻风丧胆：\"撼山易，撼岳家军难！\"\n\n1140年，岳飞北伐，连战连捷，直逼开封。收复中原，指日可待。\n\n然而，十二道金牌，将他召回。秦桧以\"莫须有\"的罪名，将他杀害于风波亭。\n\n临死前，他写下八个字：天日昭昭，天日昭昭。\n\n他活了39岁，却永远活在中华民族的血脉里。"
  },

  jiangsu: {
    fullName: "韩信",
    era: "西汉",
    dynasty: "汉",
    birthYear: -231,
    deathYear: -196,
    birthPlace: "淮阴（今江苏淮安）",
    
    biography: {
      summary: "汉初三杰之一，兵仙，帮刘邦定三秦、灭魏、破代、平赵、收燕、伐齐，最后死于未央宫。",
      keyEvents: [
        { year: -206, age: 25, event: "投奔刘邦", significance: "开始军事生涯" },
        { year: -205, age: 26, event: "暗度陈仓", significance: "定三秦" },
        { year: -204, age: 27, event: "背水一战", significance: "破赵" },
        { year: -202, age: 29, event: "垓下之战", significance: "十面埋伏灭项羽" },
        { year: -196, age: 35, event: "死于未央宫", significance: "飞鸟尽，良弓藏" }
      ]
    },
    
    abilities: {
      political: { score: 30, desc: "政治幼稚，功高震主" },
      military: { score: 100, desc: "兵仙，战无不胜" },
      literary: { score: 40, desc: "军事著作（已失传）" },
      artistic: { score: 25, desc: "无记载" },
      strategic: { score: 99, desc: "战略布局，举世无双" },
      charisma: { score: 75, desc: "军中威望高，但无政治根基" },
      innovation: { score: 98, desc: "暗度陈仓、背水一战，战法创新" },
      leadership: { score: 95, desc: "多多益善" }
    },
    
    achievements: [
      { title: "暗度陈仓", year: -205, impact: 9, desc: "出奇制胜，定三秦" },
      { title: "背水一战", year: -204, impact: 9, desc: "置之死地而后生" },
      { title: "垓下之战", year: -202, impact: 10, desc: "十面埋伏，灭项羽" },
      { title: "被尊为兵仙", year: -202, impact: 10, desc: "中国军事史上兵家巅峰" }
    ],
    
    story: "【兵仙韩信】\n\n他年轻时，被街头屠夫羞辱，从对方胯下爬过——这就是\"胯下之辱\"的典故。\n\n他离开项羽，投奔刘邦，却只做了个管粮草的小官。他决定离开，萧何连夜追赶，留下了\"萧何月下追韩信\"的佳话。\n\n刘邦终于重用他。韩信也不负众望，战无不胜：暗度陈仓、背水一战、十面埋伏、四面楚歌。\n\n他帮刘邦打下天下，被封为齐王，后又贬为淮阴侯。\n\n他想起了范蠡的话：飞鸟尽，良弓藏；狡兔死，走狗烹。\n\n公元前196年，吕后与萧何合谋，将韩信骗入未央宫杀害。\n\n\"成也萧何，败也萧何。\"兵仙韩信，死于自己最信任的人手中。"
  },

  shandong: {
    fullName: "孙武",
    era: "春秋",
    dynasty: "吴国",
    birthYear: -545,
    deathYear: -470,
    birthPlace: "齐国乐安（今山东惠民）",
    
    biography: {
      summary: "春秋时期军事家，兵圣，著《孙子兵法》，影响世界军事思想两千多年。",
      keyEvents: [
        { year: -515, age: 30, event: "献兵法于吴王", significance: "被重用为将" },
        { year: -512, age: 33, event: "著《孙子兵法》", significance: "千古兵家圣典" },
        { year: -506, age: 39, event: "柏举之战", significance: "大败楚国，入郢都" }
      ]
    },
    
    abilities: {
      political: { score: 85, desc: "辅佐吴王阖闾，强吴称霸" },
      military: { score: 100, desc: "兵圣，军事理论巅峰" },
      literary: { score: 98, desc: "《孙子兵法》，影响深远" },
      artistic: { score: 50, desc: "无记载" },
      strategic: { score: 100, desc: "战略思想超前" },
      charisma: { score: 80, desc: "兵家推崇，万世师表" },
      innovation: { score: 100, desc: "开创军事理论体系" },
      leadership: { score: 88, desc: "训练女兵，军纪严明" }
    },
    
    achievements: [
      { title: "著《孙子兵法》", year: -512, impact: 10, desc: "世界军事理论第一书" },
      { title: "柏举之战", year: -506, impact: 9, desc: "以三万破二十万" },
      { title: "辅佐吴王称霸", year: -506, impact: 8, desc: "吴国成为春秋霸主" }
    ],
    
    story: "【兵圣】\n\n\"知彼知己，百战不殆。\"\n\n这句话，出自《孙子兵法》，影响了世界两千多年。\n\n孙武，生于齐国，却投奔吴国。他把兵法十三篇献给吴王阖闾，吴王问他：\"你可以训练女兵吗？\"\n\n孙武答应了。他让吴王的宫女排队训练，宫女们嬉笑不止。孙武下令斩杀两名带头嬉笑的宠妃。\n\n从此，宫女们令行禁止。\n\n吴王惊呆了，从此重用孙武。孙武帮助吴国打败楚国，入郢都，称霸一时。\n\n功成身退，孙武隐居山林。他留下的《孙子兵法》，成为世界军事理论的宝典。\n\n他被称为\"兵圣\"，当之无愧。"
  },

  anhui: {
    fullName: "朱元璋",
    era: "明朝",
    dynasty: "明",
    birthYear: 1328,
    deathYear: 1398,
    birthPlace: "濠州钟离（今安徽凤阳）",
    
    biography: {
      summary: "明朝开国皇帝，从乞丐到皇帝，驱逐蒙元，恢复中华，建立大明王朝。",
      keyEvents: [
        { year: 1344, age: 16, event: "出家为僧", significance: "饥荒中求生" },
        { year: 1352, age: 24, event: "投奔红巾军", significance: "开始军事生涯" },
        { year: 1368, age: 40, event: "建立明朝", significance: "驱逐蒙元，恢复中华" },
        { year: 1398, age: 70, event: "病逝", significance: "洪武之治结束" }
      ]
    },
    
    abilities: {
      political: { score: 98, desc: "雄才大略，集权统治" },
      military: { score: 94, desc: "战无不胜，用兵如神" },
      literary: { score: 50, desc: "出身贫寒，自学成才" },
      artistic: { score: 35, desc: "无特别兴趣" },
      strategic: { score: 96, desc: "高筑墙、广积粮、缓称王" },
      charisma: { score: 85, desc: "威严霸气，但手段残忍" },
      innovation: { score: 85, desc: "废除丞相，设立锦衣卫" },
      leadership: { score: 98, desc: "驾驭群臣，铁腕治国" }
    },
    
    achievements: [
      { title: "驱逐蒙元", year: 1368, impact: 10, desc: "恢复华夏政权" },
      { title: "建立明朝", year: 1368, impact: 10, desc: "延续276年" },
      { title: "洪武之治", year: 1398, impact: 9, desc: "社会恢复发展" },
      { title: "废除丞相制度", year: 1380, impact: 8, desc: "君主专制达到顶峰" }
    ],
    
    story: "【乞丐皇帝】\n\n他出生在安徽凤阳一个贫苦农民家庭。16岁那年，饥荒和瘟疫夺走了他的父母和兄长。\n\n他无路可走，入皇觉寺为僧。后来寺庙也没饭吃了，他只能四处乞讨。\n\n他叫朱元璋，当时还叫朱重八。\n\n他投奔了红巾军，从一个十夫长做起。他作战勇敢，智谋过人，很快脱颖而出。\n\n\"高筑墙、广积粮、缓称王。\"这是他的战略。他先消灭陈友谅、张士诚，再北伐中原。\n\n1368年，他在南京称帝，建立大明王朝。他驱逐蒙元，恢复中华，成为历史上唯一一个从乞丐到皇帝的人。"
  },

  fujian: {
    fullName: "郑成功",
    era: "明末清初",
    dynasty: "南明",
    birthYear: 1624,
    deathYear: 1662,
    birthPlace: "日本平户",
    
    biography: {
      summary: "明末清初军事家，收复台湾，被尊为国姓爷。",
      keyEvents: [
        { year: 1646, age: 22, event: "父亲降清", significance: "坚决抗清" },
        { year: 1655, age: 31, event: "被封为延平郡王", significance: "南明封赏" },
        { year: 1661, age: 37, event: "收复台湾", significance: "驱逐荷兰殖民者" },
        { year: 1662, age: 38, event: "病逝", significance: "壮志未酬" }
      ]
    },
    
    abilities: {
      political: { score: 85, desc: "经营台湾，建立政权" },
      military: { score: 95, desc: "水师名将，收复台湾" },
      literary: { score: 60, desc: "能诗文" },
      artistic: { score: 45, desc: "无特别记载" },
      strategic: { score: 90, desc: "东征台湾，战略眼光" },
      charisma: { score: 92, desc: "忠义精神，万世敬仰" },
      innovation: { score: 80, desc: "发展海军，建设台湾" },
      leadership: { score: 92, desc: "父子决裂，忠贞不渝" }
    },
    
    achievements: [
      { title: "收复台湾", year: 1661, impact: 10, desc: "驱逐荷兰殖民者" },
      { title: "经营台湾", year: 1662, impact: 9, desc: "开发台湾，传播中华文化" },
      { title: "坚决抗清", year: 1646, impact: 8, desc: "忠义精神" }
    ],
    
    story: "【国姓爷】\n\n他的父亲郑芝龙投降了清朝，他跪在父亲面前痛哭，父亲不听。\n\n他走了，带着自己的部下，竖起抗清的大旗。皇帝赐他姓朱，称为\"国姓爷\"。\n\n他想过反攻大陆，但最终还是失败了。他把目光投向了东方——台湾。\n\n1661年，他率领两万五千大军，横渡台湾海峡。九个月后，荷兰殖民者投降。\n\n台湾，回到了中国人的手中。\n\n可惜，他收复台湾不到半年就病倒了。临终前，他说：\"吾死何憾，唯恨志未酬耳。\"\n\n他活了38岁，但他的名字，永远刻在了历史的丰碑上。"
  },

  neimenggu: {
    fullName: "铁木真",
    era: "蒙古帝国",
    dynasty: "蒙古",
    birthYear: 1162,
    deathYear: 1227,
    birthPlace: "斡难河畔",
    
    biography: {
      summary: "成吉思汗，蒙古帝国创建者，统一蒙古草原，征服半个世界。",
      keyEvents: [
        { year: 1189, age: 27, event: "被推举为蒙古可汗", significance: "开始统一征程" },
        { year: 1206, age: 44, event: "建立蒙古帝国", significance: "尊号成吉思汗" },
        { year: 1211, age: 49, event: "伐金", significance: "开始对外扩张" },
        { year: 1219, age: 57, event: "西征花剌子模", significance: "征服中亚" },
        { year: 1227, age: 65, event: "病逝于西夏", significance: "一代天骄陨落" }
      ]
    },
    
    abilities: {
      political: { score: 95, desc: "统一草原，建立帝国" },
      military: { score: 100, desc: "征服半个世界" },
      literary: { score: 30, desc: "文盲但重视文化" },
      artistic: { score: 35, desc: "不拘一格" },
      strategic: { score: 99, desc: "战略目光远大" },
      charisma: { score: 99, desc: "天生的领袖" },
      innovation: { score: 92, desc: "创立蒙古文字，建立千户制" },
      leadership: { score: 100, desc: "众汗之汗" }
    },
    
    achievements: [
      { title: "统一蒙古草原", year: 1206, impact: 9, desc: "结束草原分裂" },
      { title: "建立蒙古帝国", year: 1206, impact: 10, desc: "世界历史上最大的陆上帝国" },
      { title: "西征花剌子模", year: 1219, impact: 9, desc: "打通东西方通道" },
      { title: "创立蒙古文字", year: 1204, impact: 8, desc: "文化传承的载体" }
    ],
    
    story: "【一代天骄】\n\n他出生时，手握凝血如石。草原上的萨满说：\"这孩子，将来必成大器。\"\n\n他叫铁木真。九岁那年，父亲被仇人毒死。部落抛弃了他们一家，母亲带着他们在草原上艰难求生。\n\n\"影子是最好的朋友。\"他从小就知道，只能靠自己。\n\n他召集旧部，开始征战。一统蒙古草原，建立了蒙古帝国。他被尊称为\"成吉思汗\"，意为\"众汗之汗\"。\n\n他率领蒙古铁骑，征服了半个世界：西夏、金国、花剌子模...他的孙子忽必烈建立了元朝。\n\n1227年，他在征讨西夏途中病逝。他的陵墓至今成谜。\n\n\"一代天骄，成吉思汗，只识弯弓射大雕。\"毛泽东这样评价他。"
  }
};

// 获取人物详细数据
function getFigureDetail(provinceKey) {
  return figureDetails[provinceKey] || null;
}

// 计算综合能力评分
function calculateOverallScore(abilities) {
  const weights = {
    political: 0.15,
    military: 0.18,
    literary: 0.08,
    artistic: 0.05,
    strategic: 0.18,
    charisma: 0.12,
    innovation: 0.10,
    leadership: 0.14
  };
  
  let total = 0;
  for (const key in weights) {
    if (abilities[key]) {
      total += abilities[key].score * weights[key];
    }
  }
  return Math.round(total);
}

// 获取能力等级
function getAbilityRank(score) {
  if (score >= 90) return 'S';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  return 'D';
}