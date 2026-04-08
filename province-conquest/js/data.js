// 省份代表人物数据
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