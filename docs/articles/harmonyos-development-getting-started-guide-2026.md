# 鸿蒙开发上手实录：30分钟写出你的第一个App

我第一次装DevEco Studio的时候，光配置环境就搞了2小时。

回头看，其实不该这么难。是我没人带路踩坑了。

这篇文章还你一个教训。我带你完整走一遍。30分钟，让你做出第一个能跑的鸿蒙App。

不需要你会什么高深的技术。只要你有过开发经验，就能跟着做。

## 环境准备（10分钟）

### 1. 下载DevEco Studio

去华为开发者官网：developer.harmonyos.com

找到“下载”→ 选择你的系统版本 → 下载安装包。

Windows用户双击运行，一直点“下一步”就装好了。

Mac用户拖拽到Applications文件夹。

Linux用户解压到/opt目录。

### 2. 配置SDK

第一次打开DevEco Studio，会弹出SDK配置窗口。

点击“Settings” → “SDK” → 下载需要的SDK。

选哪个版本？选最新的就行。现在是API 12+。

### 3. 登录华为账号

点右上角“Sign In”。去华为开发者官网注册一个账号。

这个账号用来上传应用到应用市场，必需。

## 创建项目（5分钟）

### 1. 新建项目

File → New Project

左边选“Empty Ability”（空模板，最干净）

右边填：
- Name: MyFirstApp
- Bundle name: com.example.myfirstapp
- Device: Phone（手机）
- Language: ArkTS

点Finish。项目创建完成。

### 2. 认识项目结构

创建好的项目，长这样：

```
MyFirstApp/
├── src/
│   └── main/
│       └── ets/
│           └── entry/
│               ├── entryability.ts    // 程序入口
│               └── pages/
│                   └── index.ets     // 第一个页面
├── module.json5                    // 配置文件
└── oh-package.json5                // 依赖管理
```

就三个关键文件。别的先不管。

entryability.ts 是程序入口，类似Android的Application。

index.ets 是页面。ets是Extended TypeScript，鸿蒙的UI文件。

## 写代码（10分钟）

打开index.ets。删除默认代码，换成下面这个：

### 完整代码：计数器

```typescript
// 导入需要的组件
import { Button, Column, Text } from '@kit.ArkUI'

// @Entry = 入口页面
// @Component = 这是一个组件
@Entry
@Component
struct Index {
  // @State = 响应式变量。变量变化，UI自动更新
  @State count: number = 0

  build() {
    // Column = 垂直布局
    Column({ space: 20 }) {
      // 显示数字，大字
      Text(`计数: ${this.count}`)
        .fontSize(50)
        .fontWeight(FontWeight.Bold)

      // 加1按钮
      Button('点我+1')
        .type(ButtonType.Capsule)
        .onClick(() => {
          this.count++
        })

      // 重置按钮
      Button('重置')
        .type(ButtonType.Capsule)
        .backgroundColor('#FF6B6B')
        .onClick(() => {
          this.count = 0
        })
    }
    // 样式
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }
}
```

这段代码做了什么事：

1. 定义了一个变量count，初始值0
2. 页面上显示这个数字
3. 点了“+1”按钮，数字加1
4. 点了“重置”按钮，数字归零

响应式就在这里：@State声明的变量变化时，UI自动刷新。不用像以前Android那样findViewById。

## 运行（5分钟）

### 方式1：模拟器

点顶部工具栏的Run（三角形图标）

第一次会提示下载模拟器镜像，按提示操作。

选鸿蒙模拟器，点OK。

等待编译。首次编译要下载依赖，3到5分钟。

编译成功，模拟器上���显示你的页面。

### 方式2：真机（推荐）

1. 用USB连手机
2. 手机开启“开发者选项”→“USB调试”
3. 识别到设备后，选中手机，点Run

手机屏幕亮起，你的App跑起来了。

## 常见问题（我踩过的坑）

### Q1：编译报错找不到模块

通常是SDK没配好。

解决：Settings → SDK → 检查API版本是否下载成功。

### Q2：模拟器启动失败

Windows需要开启虚拟化。

解决：重启电脑，进BIOS开启Intel VT-x。

或者直接用真机，更省心。

### Q3：页面不刷新

检查变量是否用了@State。

解决：只有@State声明的变量才能触发UI更新。

### Q4：样式不生效

鸿蒙不用CSS文件。

解决：链式调用设置样式，比如`.fontSize(30).fontWeight(FontWeight.Bold)`

### Q5：手机识别不到

检查手机是否开启开发者选项，和USB调试。

华为手机需要登录华为账号才能开启开发者选项。

## 下一步学什么

跑通第一个App，你已经入门了。

接下来学什么，我给你列个路标：

| 阶段 | 学什么 | 预计时间 |
|------|--------|----------|
| 进阶1 | 更多组件：Image、List、Grid | 1周 |
| 进阶2 | 页面跳转：router.pushRouter | 2天 |
| 进阶3 | 网络请求：fetch调API | 1周 |
| 进阶4 | 数据存储：用户首选项 | 3天 |
| 进阶5 | 发布上架：签名+华为应用市场 | 2天 |

这五关过了，你就是一个能干的鸿蒙开发者了。

## 资源汇总

| 资源 | 地址 |
|------|------|
| DevEco Studio | developer.harmonyos.com |
| 官方文档 | developer.harmonyos.com/cn/docs |
| ArkTS语法 | docs.openharmony.cn |
| 开发者论坛 | bbs.huawei.com |

先收藏。用的时候随时查。

---

**配套阅读：**

- 《2026年鸿蒙开发：为什么我现在劝你入局？》- 了解为什么要学
- 《ArkTS核心语法详解》- 深入学ArkTS