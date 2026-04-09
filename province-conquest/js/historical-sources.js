// ========================================
// 历史人物学术验证与文献来源
// 历史学家角色学术审查
// ========================================

/**
 * 学术可信度等级说明
 * ★★★ 文献充分 - 有一手史料支持，学术共识明确
 * ★★☆ 学术共识 - 二手研究为主，存在少量争议
 * ★☆☆ 有争议 - 史料不足或存疑，需要学术讨论
 */

const historicalSources = {
  // ===== 秦始皇 =====
  shaanxi: {
    sources: {
      primary: [
        "《史记·秦始皇本纪》- 司马迁，约公元前91年",
        "《史记·李斯列传》- 司马迁",
        "《战国策》- 刘向编订",
        "秦简出土文物（睡虎地秦简、里耶秦简）- 一手考古材料",
        "秦始皇陵兵马俑考古发掘报告"
      ],
      secondary: [
        "《秦汉史》- 吕思勉",
        "《秦始皇传》- 张分田",
        "《秦史》- 林剑鸣",
        "《剑桥中国秦汉史》- 鲁惟一主编"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: -259,
        source: "《史记·秦始皇本纪》：'以秦昭王四十八年正月生于邯郸'",
        credibility: "★★★",
        note: "有明确记载，可信度高"
      },
      deathYear: {
        recorded: -210,
        source: "《史记·秦始皇本纪》：'七月丙寅，始皇崩于沙丘平台'",
        credibility: "★★★",
        note: "史有明文"
      },
      birthPlace: {
        claimed: "邯郸（今河北邯郸）",
        source: "《史记》：'秦昭王四十八年正月生于邯郸'",
        credibility: "★★★",
        note: "异人质赵期间所生，有明确记载"
      },
      unifications: {
        source: "《史记·秦始皇本纪》详载统一过程",
        timeline: [
          { year: -230, kingdom: "韩", method: "内史腾率军攻灭" },
          { year: -229, kingdom: "赵", method: "王翦攻破邯郸" },
          { year: -225, kingdom: "魏", method: "王贲水淹大梁" },
          { year: -223, kingdom: "楚", method: "王翦六十万大军灭楚" },
          { year: -222, kingdom: "燕", method: "王贲攻下辽东" },
          { year: -221, kingdom: "齐", method: "王贲南下灭齐" }
        ],
        credibility: "★★★"
      }
    },
    
    historiographicalNotes: {
      controversies: [
        {
          issue: "生父争议",
          claim: "吕不韦之子说",
          source: "《史记·吕不韦列传》载'姬自匿有身'",
          academicConsensus: "主流史学界认为此说不可信，《史记》本身记载矛盾。秦庄襄王在赵国为人质，娶赵姬生子嬴政于前259年。'吕不韦之子'可能是后世抹黑。",
          conclusion: "★☆☆ 有争议 - 学术界主流认为为秦庄襄王之子"
        },
        {
          issue: "焚书坑儒人数",
          claim: "坑杀四百六十余人",
          source: "《史记·秦始皇本纪》",
          academicConsensus: "数字确切，《史记》记载可信。但后世对'坑儒'性质有争议——可能是江湖术士而非儒生。",
          conclusion: "★★☆ 学术共识 - 事件存在，性质有争议"
        }
      ],
      materialCulture: {
        dailyLife: "秦代制度改革：统一度量衡（商鞅方升存世）、统一文字（小篆）、统一货币（秦半两钱）",
        architecture: "阿房宫遗址考古发现前殿夯土台基，东西长1270米，南北宽426米",
        military: "兵马俑出土武士俑约8000件，战车130余辆，陶马600余匹",
        technology: "秦代冶铁技术成熟，秦剑多为青铜材质，长度约81-94厘米"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "司马迁",
        era: "西汉",
        evaluation: "秦王怀贪鄙之心，行自奋之智，不信功臣，不亲士民，废王道，立私权，禁文书而酷刑法，先诈力而后仁义，以暴虐为天下始。",
        source: "《史记·秦始皇本纪》"
      },
      {
        scholar: "贾谊",
        era: "西汉",
        evaluation: "一夫作难而七庙隳，身死人手，为天下笑者，何也？仁义不施而攻守之势异也。",
        source: "《过秦论》"
      },
      {
        scholar: "柳宗元",
        era: "唐",
        evaluation: "秦之所以革之者，其为制，公之大者也；其情，私也，私其一己之威也，私其尽臣畜于我也。然而公天下之端自秦始。",
        source: "《封建论》"
      },
      {
        scholar: "钱穆",
        era: "现代",
        evaluation: "秦始皇统一六国，为中国历史上开天辟地之创举，其事业之伟大，无可否认。",
        source: "《国史大纲》"
      }
    ]
  },

  // ===== 李广 =====
  gansu: {
    sources: {
      primary: [
        "《史记·李将军列传》- 司马迁",
        "《汉书·李广苏建传》- 班固",
        "居延汉简 - 出土汉代边疆文书"
      ],
      secondary: [
        "《汉代人物传》- 吕思勉",
        "《西汉会要》- 徐天麟",
        "《史记研究》- 张大可"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: "约-183",
        source: "推算，《史记》载文帝十四年（-166）从军时年约十七",
        credibility: "★☆☆",
        note: "生年无明确记载，据从军年龄推算，有约10年误差可能"
      },
      deathYear: {
        recorded: -119,
        source: "《史记·李将军列传》：'广遂引刀自刭'",
        credibility: "★★★",
        note: "有明确记载，漠北之战迷路自尽"
      },
      family: {
        origin: "陇西成纪（今甘肃天水秦安县）",
        background: "将门世家，先祖李信为秦将",
        source: "《史记》：'其先曰李信，秦时为将'",
        credibility: "★★★"
      }
    },
    
    historiographicalNotes: {
      keyBattles: [
        {
          battle: "上郡之战",
          year: -144,
          source: "《史记》",
          events: "李广率百骑遇匈奴数千骑，佯装诱敌，匈奴疑有伏兵而退",
          significance: "体现其临危不乱的军事才能"
        },
        {
          battle: "雁门之战",
          year: -129,
          source: "《史记》",
          events: "兵败被俘，佯死夺马逃回",
          significance: "被判死罪，赎为庶人"
        },
        {
          battle: "右北平之战",
          year: -121,
          source: "《史记》",
          events: "率四千骑被围，激战两日，援军至解围",
          significance: "展现骑射战术能力"
        }
      ],
      "飞将军"称号: {
        source: "《史记》：'广居右北平，匈奴闻之，号曰「汉之飞将军」，避之数岁，不敢入右北平'",
        meaning: "匈奴对其骑兵机动能力的敬畏",
        credibility: "★★★"
      },
      "李广难封": {
        source: "《史记》载文帝语：'惜乎，子不遇时！如令子当高帝时，万户侯岂足道哉！'",
        analysis: "李广一生征战七十余次，历任七郡太守，始终未能封侯。原因分析：1.战略层面贡献有限 2.政治斗争能力不足 3.运气不佳（迷路、被俘等）",
        academicDebate: "王充《论衡》认为是命；现代学者多认为是其战术能力与政治情商不成正比"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "司马迁",
        era: "西汉",
        evaluation: "余睹李将军，悛悛如鄙人，口不能道辞。及死之日，天下知与不知，皆为尽哀。彼其忠实心诚信于士大夫也。谚曰：'桃李不言，下自成蹊'。此言虽小，可以喻大也。",
        source: "《史记·李将军列传》"
      },
      {
        scholar: "王昌龄",
        era: "唐",
        evaluation: "秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。",
        source: "《出塞》"
      }
    ],
    
    materialCulture: {
      weaponry: "汉代骑兵主要装备：环首刀、弓箭（李广善射）、长戟",
      horseArchery: "骑射是汉军对抗匈奴的核心技能，《史记》载'广为人长，猿臂，其善射亦天性也'",
      frontierLife: "居延汉简记载汉代边疆士兵生活：每日口粮约2升粟米，月俸约600钱"
    }
  },

  // ===== 诸葛亮 =====
  henan: {
    sources: {
      primary: [
        "《三国志·蜀书·诸葛亮传》- 陈寿",
        "《三国志》裴松之注引《魏略》《襄阳记》等",
        "诸葛亮《出师表》《诫子书》- 原作存世",
        "《华阳国志》- 常璩"
      ],
      secondary: [
        "《诸葛亮传》- 田余庆",
        "《三国史》- 马植杰",
        "《三国志集解》- 卢弼"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: 181,
        source: "《三国志》：光和四年（181年）生于琅琊阳都",
        credibility: "★★★"
      },
      deathYear: {
        recorded: 234,
        source: "《三国志》：建兴十二年（234年）秋八月，亮疾病，卒于军，时年五十四",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "琅琊阳都（今山东沂南县）",
        source: "《三国志》",
        credibility: "★★★",
        note: "籍贯琅琊，幼年随叔父避乱至荆州"
      }
    },
    
    historiographicalNotes: {
      "三顾茅庐": {
        source: "《三国志》：'由是先主遂诣亮，凡三往，乃见'",
        credibility: "★★★",
        note: "陈寿记载可信，但具体情节《三国演义》有艺术加工"
      },
      "隆中对": {
        source: "《三国志》载诸葛亮与刘备对话全文",
        content: "北让曹操，东和孙权，先取荆州、益州",
        credibility: "★★★",
        note: "三国鼎立的理论基础，有确切史文"
      },
      "赤壁之战": {
        role: "诸葛亮出使东吴，促成孙刘联盟",
        source: "《三国志·诸葛亮传》《周瑜传》",
        credibility: "★★★",
        note: "实际军事指挥以周瑜为主，诸葛亮功在外交"
      },
      "北伐": {
        times: "五次北伐（非六出祁山）",
        source: "《三国志》本传",
        timeline: [
          { year: 228, result: "失街亭，斩马谡" },
          { year: 228, result: "围陈仓不克" },
          { year: 229, result: "取武都、阴平" },
          { year: 231, result: "粮尽退军，射杀张郃" },
          { year: 234, result: "五丈原病逝" }
        ]
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "陈寿",
        era: "西晋",
        evaluation: "诸葛亮之为相国也，抚百姓，示仪轨，约官职，从权制，开诚心，布公道...可谓识治之良才，管、萧之亚匹矣。然连年动众，未能成功，盖应变将略，非其所长欤！",
        source: "《三国志·诸葛亮传》"
      },
      {
        scholar: "司马懿",
        era: "三国",
        evaluation: "天下奇才也。",
        source: "《三国志》裴注引《魏氏春秋》"
      }
    ],
    
    materialCulture: {
      "木牛流马": {
        source: "《三国志》载诸葛亮'性长于巧思，损益连弩，木牛流马，皆出其意'",
        nature: "山地运输工具，具体形制已失传",
        academicDebate: "学界对其原理有多种推测：独轮车说、四轮车说、连杆机构说"
      },
      "诸葛连弩": {
        source: "《三国志》载'损益连弩'",
        nature: "改良版连弩，可一弩十矢",
        credibility: "★★☆"
      }
    }
  },

  // ===== 岳飞 =====
  zhejiang: {
    sources: {
      primary: [
        "《宋史·岳飞传》- 脱脱等",
        "《鄂国金佗稡编》- 岳珂（岳飞之孙）",
        "《建炎以来系年要录》- 李心传",
        "《三朝北盟会编》- 徐梦莘"
      ],
      secondary: [
        "《岳飞传》- 邓广铭",
        "《岳飞新传》- 王曾瑜",
        "《宋史研究集》"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: 1103,
        source: "《宋史》：崇宁二年（1103年）生于相州汤阴",
        credibility: "★★★"
      },
      deathYear: {
        recorded: 1142,
        source: "《宋史》：绍兴十一年十二月二十九日（1142年1月27日），赐死于大理寺",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "相州汤阴（今河南汤阴）",
        source: "《宋史》",
        credibility: "★★★",
        note: "岳飞出生地有明确记载"
      }
    },
    
    historiographicalNotes: {
      "精忠报国刺字": {
        source: "《宋史》无记载，始见于元杂剧和明小说",
        credibility: "★☆☆",
        academicConsensus: "刺字故事可能是后世艺术加工，但岳飞忠心报国确有史实依据"
      },
      "岳家军军纪": {
        source: "《宋史》：'冻死不拆屋，饿死不掳掠'",
        credibility: "★★★",
        materialBasis: "南宋初期约10万兵力，财政依赖朝廷供给和地方税收"
      },
      "郾城大捷": {
        year: 1140,
        source: "《宋史》本传",
        significance: "以步兵对抗金军重骑兵，创克制重骑兵战术",
        credibility: "★★★"
      },
      "十二道金牌": {
        source: "《宋史》载'秦桧以飞不死，乃以先诏趣飞班师'",
        credibility: "★★☆",
        note: "诏令班师是事实，'十二道'可能是艺术夸张"
      },
      "莫须有": {
        source: "《宋史》载韩世忠问秦桧：'飞子云与张宪书虽不明，其事体莫须有'",
        credibility: "★★★",
        note: "秦桧以'莫须有'（可能有的意思）定罪"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "宋孝宗",
        era: "南宋",
        evaluation: "卿家纪律，用兵如神，战胜攻取，得其死力。有功不伐，有德不轩，无愧古人。",
        source: "赐岳飞谥号敕"
      },
      {
        scholar: "文天祥",
        era: "南宋",
        evaluation: "岳先生，我宋之吕尚也。建功树绩，载在史册，千百世后，如见其生。",
        source: "《指南录》"
      }
    ]
  },

  // ===== 韩信 =====
  jiangsu: {
    sources: {
      primary: [
        "《史记·淮阴侯列传》- 司马迁",
        "《汉书·韩信传》- 班固",
        "《史记·高祖本纪》"
      ],
      secondary: [
        "《楚汉春秋》- 陆贾（已散佚，部分存于《史记》注）",
        "《韩信研究》"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: "约-231",
        source: "推算，《史记》载韩信约与刘邦同辈，较张良年轻",
        credibility: "★☆☆",
        note: "生年无明确记载"
      },
      deathYear: {
        recorded: -196,
        source: "《史记》：汉高祖十一年，吕后使萧何诱韩信入宫，杀于长乐宫钟室",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "淮阴（今江苏淮安淮阴区）",
        source: "《史记》：'淮阴侯韩信者，淮阴人也'",
        credibility: "★★★"
      }
    },
    
    historiographicalNotes: {
      "胯下之辱": {
        source: "《史记》：淮阴屠中少年侮信，信熟视之，俯出袴下",
        credibility: "★★☆",
        note: "司马迁记载，但具体细节可能有艺术加工"
      },
      "背水一战": {
        battle: "井陉之战",
        year: -204,
        source: "《史记》详载",
        tactic: "置之死地而后生，以三万破赵二十万",
        credibility: "★★★"
      },
      "十面埋伏": {
        battle: "垓下之战",
        year: -202,
        source: "《史记》记载韩信设围攻项羽",
        credibility: "★★★",
        note: "'十面埋伏'多数是后世演义说法"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "司马迁",
        era: "西汉",
        evaluation: "吾如淮阴，淮阴人为余言，韩信虽为布衣时，其志与众异。其母死，贫无以葬，然乃行营高敞地，令其旁可置万家。余视其母冢，良然。",
        source: "《史记·淮阴侯列传》"
      },
      {
        scholar: "刘邦",
        era: "西汉",
        evaluation: "连百万之军，战必胜，攻必取，吾不如韩信。",
        source: "《史记·高祖本纪》"
      }
    ]
  },

  // ===== 孙武 =====
  shandong: {
    sources: {
      primary: [
        "《史记·孙子吴起列传》- 司马迁",
        "《孙子兵法》- 孙武著（出土版本：银雀山汉简）",
        "《左传》- 左丘明"
      ],
      secondary: [
        "《孙子兵法研究》",
        "《中国兵学史》"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: "约-545",
        source: "推算，依据生卒年记载约与孔子同时",
        credibility: "★☆☆",
        note: "生卒年有较大争议，有学者怀疑孙武是否确有其人"
      },
      deathYear: {
        recorded: "约-470",
        source: "推算",
        credibility: "★☆☆"
      },
      birthPlace: {
        claimed: "齐国乐安（今山东惠民，一说广饶）",
        source: "《史记》",
        credibility: "★★☆",
        note: "籍贯有争议，山东惠民和广饶都说自己是孙武故里"
      }
    },
    
    historiographicalNotes: {
      existenceDebate: {
        issue: "孙武是否确有其人",
        controversy: "有学者认为孙武可能是孙膑的讹传或综合人物",
        evidence: "1972年银雀山汉简同时出土《孙子兵法》和《孙膑兵法》，证明两人确非同一人",
        academicConsensus: "★★☆ - 孙武存在可能性较高，但生平细节存疑"
      },
      "柏举之战": {
        year: -506,
        source: "《左传》定公四年",
        events: "吴国孙武、伍子胥辅佐吴王阖闾大破楚军，五战入郢",
        credibility: "★★★"
      },
      "吴宫教战": {
        source: "《史记》载斩杀吴王宠妃以立军纪",
        credibility: "★☆☆",
        note: "可能是后世附会的故事"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "司马迁",
        era: "西汉",
        evaluation: "阖庐知孙子能用兵，卒以为将。西破强楚，入郢；北威齐晋，显名诸侯，孙子与有力焉。",
        source: "《史记·孙子吴起列传》"
      }
    ]
  },

  // ===== 朱元璋 =====
  anhui: {
    sources: {
      primary: [
        "《明太祖实录》- 官方编修",
        "《明史·太祖本纪》- 张廷玉等",
        "《明通鉴》- 夏燮",
        "朱元璋亲撰《皇陵碑》"
      ],
      secondary: [
        "《朱元璋传》- 吴晗",
        "《明史讲义》- 孟森",
        "《明初政治史》"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: 1328,
        source: "《明史》：天历元年（1328年）生于濠州钟离太平乡孤庄村",
        credibility: "★★★"
      },
      deathYear: {
        recorded: 1398,
        source: "《明史》：洪武三十一年闰五月初十日崩于西宫",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "濠州钟离（今安徽凤阳）",
        source: "《明史》",
        credibility: "★★★"
      },
      family: {
        father: "朱世珍（原名朱五四）",
        mother: "陈氏",
        siblings: "四兄二姐，饥荒中多饿死"
      }
    },
    
    historiographicalNotes: {
      "乞讨经历": {
        source: "朱元璋亲撰《皇陵碑》记载：'依亲友刘氏兄弟，继而衣食不给'",
        credibility: "★★★",
        note: "朱元璋亲述早年艰辛，有官方碑文可证"
      },
      "红巾军": {
        year: 1352,
        source: "《明史》",
        events: "投奔郭子兴起兵，从九夫长做起",
        credibility: "★★★"
      },
      "高筑墙、广积粮、缓称王": {
        source: "《明史·朱升传》载朱升献策",
        credibility: "★★★"
      },
      "废除丞相": {
        year: 1380,
        source: "《明史》",
        events: "胡惟庸案后废除丞相制度",
        impact: "君主专制度达顶峰，影响明清两代"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "赵翼",
        era: "清",
        evaluation: "圣贤、豪杰、盗贼之性，实兼而有之者也。",
        source: "《二十二史札记》"
      },
      {
        scholar: "毛泽东",
        era: "现代",
        evaluation: "朱元璋是农民起义领袖，是应该肯定的，应该写的好一点，不要写得那么坏。",
        source: "谈话记录"
      }
    ]
  },

  // ===== 郑成功 =====
  fujian: {
    sources: {
      primary: [
        "《台湾通史》- 连横",
        "《清史稿·郑成功传》",
        "《海上见闻录》- 阮旻锡",
        "《先王实录》（郑氏档案）"
      ],
      secondary: [
        "《郑成功传》- 朱希祖",
        "《郑成功研究》"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: 1624,
        source: "《台湾通史》",
        credibility: "★★★"
      },
      deathYear: {
        recorded: 1662,
        source: "《清史稿》、《台湾通史》",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "日本平户（今长崎县平户市）",
        source: "多部史料记载郑芝龙在日本经商期间娶妻田川氏",
        credibility: "★★★"
      }
    },
    
    historiographicalNotes: {
      "国姓爷": {
        source: "南明隆武帝赐姓朱，名成功",
        credibility: "★★★"
      },
      "收复台湾": {
        year: 1661,
        source: "《台湾通史》详载",
        forces: "率2.5万大军、300余艘战船",
        battle: "围困热兰遮城9个月，1662年2月1日荷兰总督揆一投降",
        credibility: "★★★",
        significance: "结束荷兰38年殖民统治"
      },
      "父子决裂": {
        year: 1646,
        source: "郑芝龙降清，郑成功苦谏不从",
        credibility: "★★★"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "连横",
        era: "日据台湾",
        evaluation: "成功，千古伟人也，收复台湾，我汉族伸气于海外，成功之力也。",
        source: "《台湾通史》"
      }
    ]
  },

  // ===== 成吉思汗 =====
  neimenggu: {
    sources: {
      primary: [
        "《蒙古秘史》（元朝秘史）- 蒙古文原典，1240年成书",
        "《元史·太祖本纪》- 宋濂等",
        "《圣武亲征录》- 波斯文史料",
        "《史集》- 拉施特（波斯史学家）"
      ],
      secondary: [
        "《成吉思汗传》- 朱耀廷",
        "《蒙古帝国史》- 格鲁塞"
      ]
    },
    
    academicValidation: {
      birthYear: {
        recorded: "约1162",
        source: "《蒙古秘史》、《元史》",
        credibility: "★★☆",
        note: "生年有1162、1167年等不同说法"
      },
      deathYear: {
        recorded: 1227,
        source: "《元史》：成吉思汗二十二年（1227年）死于征西夏途中",
        credibility: "★★★"
      },
      birthPlace: {
        claimed: "斡难河畔（今蒙古国肯特省）",
        source: "《蒙古秘史》",
        credibility: "★★★"
      }
    },
    
    historiographicalNotes: {
      "统一蒙古": {
        year: 1206,
        source: "《蒙古秘史》",
        events: "于斡难河源召开忽里勒台大会，被推举为成吉思汗",
        credibility: "★★★"
      },
      "蒙古文字": {
        year: "约1204",
        events: "命畏兀儿人塔塔统阿创制蒙古文字",
        credibility: "★★★"
      },
      "千户制": {
        content: "将蒙古部民编为95个千户，打破传统血缘部落组织",
        significance: "奠定蒙古帝国军事行政基础"
      }
    },
    
    scholarlyEvaluations: [
      {
        scholar: "毛泽东",
        era: "现代",
        evaluation: "一代天骄，成吉思汗，只识弯弓射大雕。俱往矣，数风流人物，还看今朝。",
        source: "《沁园春·雪》"
      }
    ]
  }
};

/**
 * 获取历史人物学术验证信息
 */
function getHistoricalValidation(provinceKey) {
  return historicalSources[provinceKey] || null;
}

/**
 * 导出模块
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { historicalSources, getHistoricalValidation };
}