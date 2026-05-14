# 鸿蒙开发入门完全指南

这篇文章带你在30分钟内完成鸿蒙开发的第一个APP。

不需要你会什么高深的技术。只要你有一台电脑，能上网，就够了。

## 一、开发环境准备

做鸿蒙开发，你需要准备三样东西。

### 硬件要求

电脑一台。Windows、Mac、Linux都可以。配置不需要很高。现在的电脑都能跑得动开发工具。

内存8GB以上。硬盘SSD，剩余空间20GB以上。编译项目需要存储空间。

### 软件要求

Node.js 18以上。鸿蒙的构建工具基于Node.js。

JDK 17以上。OpenJDK就可以，华为官网有下载链接。

DevEco Studio。这是鸿蒙官方IDE，基于IntelliJ IDEA二次开发。类似Android Studio的使用体验。

### 账号要求

华为开发者账号。你需要去华为开发者官网注册一个账号。这个账号用于上传应用到应用市场。

## 二、DevEco Studio安装

### 下载安装包

打开华为开发者官网，找到DevEco Studio下载页面。

Windows用户下载.exe安装包。Mac用户下载.dmg文件。Linux用户下载.tar.gz包。

下载完成后，双击安装。安装过程一路Next就可以。

### 配置SDK

第一次打开DevEco Studio时，会提示你配置SDK。

点击Settings -> SDK。下载你需要用到的SDK版本。

鸿蒙5用API 10。鸿蒙NEXT用API 12以上。根据你要开发的目标选择。

通常选择最新版本就好，不会错。

### 创建第一个项目

点击File -> New Project。

选择Empty Ability模板。这是空项目，适合入门学习。

填写项目名称。比如MyFirstApp。

填写包名。比如com.example.myfirstapp。

选择设备类型。Phone就是手机。Tablet是平板。

选择语言。这里选ArkTS。

点击Finish。项目创建成功。

## 三、项目结构认识

创建好的项目长这样。

```
MyFirstApp/
├── src/
│   ├── main/
│   │   ├── ets/
│   │   │   ├── entry/
│   │   │   │   ├── entryability.ts    // 应用入口
│   │   │   │   └── pages/
│   │   │   │       └── index.ets    // 第一个页面
│   │   └── module.json5              // 配置文件
│   └── test/                          // 测试代码
├── build-profile.json5               // 构建配置
├── hvigorfile.ts                     // 构建脚本
└── oh-package.json5                  // 依赖管理
```

看懂这三个文件就够了。

entryability.ts是应用入口，类似Android的Application类。

index.ets是第一个页面。ets是Extended TypeScript的缩写，鸿蒙的UI文件后缀。

module.json5是模块配置。包含页面路由、权限声明等。

## 四、第一个页面

现在写一个带按钮的页面。点击按钮，计数器加一。

打开index.ets文件。删除原来的默认代码，替换成以下代码。

```typescript
// 导入需要的组件
import { Button, Column, Text, StyleSheet } from '@kit.ArkUI'

// 用@Entry标记这是入口页面
@Entry
// 用@Component标记这是一个组件
@Component
struct Index {
  // @State声明变量。这个变量变化时，UI会自动更新
  @State count: number = 0

  build() {
    // Column是列布局，垂直排列子元素
    Column({ space: 20 }) {
      // 显示计数
      Text(`当前计数: ${this.count}`)
        .fontSize(30)
        .fontWeight(FontWeight.Bold)

      // 点击按钮执行这个方法
      Button('点我+1')
        .type(ButtonType.Capsule)
        .onClick(() => {
          this.count++
        })
    }
    // 设置列布局的样式
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
  }
}
```

这段代码做了什么。

定义了一个count变量，初始值是0。

页面上显示当前计数。下方有一个按钮。

点击按钮时，count加1，页面自动更新显示。

ArkTS的响应式就是这样简单。变量用@State声明，变化时UI自动更新。不需要手动刷新。

## 五、运行项目

### 模拟器运行

点击DevEco Studio顶部工具栏的Run按钮。

选择模拟器设备。鸿蒙有自己的模拟器，比真机慢但够用。

等待编译完成。首次编译需要下载依赖，时间会长一些，一般3到5分钟。

编译成功的话，模拟器上会显示你的页面。

### 真机运行

用USB连接你的华为手机。

打开手机开发者选项中的USB调试。

在DevEco Studio中选择真机设备，点击Run。

手机屏幕会显示你的应用。

## 六、常见问题

### 问题一：编译报错找不到模块

通常是SDK没配好。检查Settings -> SDK，确保对应版本的SDK已下载。

### 问题二：模拟器启动失败

模拟器需要Intel HAXM或ARM自带的虚拟化技术。Windows上可能需要去BIOS开启虚拟化。

或者直接用真机调试，更稳定。

### 问题三：页面不更新

检查变量是否用了@State声明。只有@State声明的变量变化才会触发UI更新。

### 问题四：样式不生效

检查是否在build()方法里设置样式。鸿蒙的样式在组件方法链式调用设置，而不是CSS文件。

### 问题五：真机无法识别

检查手机是否开启了开发者选项中的USB调试。华为手机需要登录华为账号才能开启。

### 问题六：API版本不兼容

不同鸿蒙版本有不同的API。开发时看清楚你要兼容的版本，选择对应的SDK。

## 七、下一步学什么

跑通了第一个APP，你已经入门了。接下来该学什么。

### 进阶一：更多UI组件

Text、Button、Column、Row是基础。还有Image、List、Stack、Grid等几十种组件需要学习。

### 进阶二：页面跳转

一个页面不够用。需要学会router.pushRouter做页面跳转，以及参数传递。

### 进阶三：网络请求

做应用不可能只做静态页面。需要学会fetch发起网络请求，调用API。

### 进阶四：数据存储

用户关闭应用后，数据还在。需要学会本地存储和数据库。

### 进阶五：发布上架

开发完成后，需要发布到华为应用市场。需要了解签名、证书、上架流程。

这五关过了，你就是一个合格的鸿蒙开发者了。

## 八、资源汇总

学习过程中需要的资源都在这里。

| 资源 | 地址 |
|------|------|
| DevEco Studio下载 | developer.harmonyos.com |
| 鸿蒙开发者文档 | developer.harmonyos.com/cn/docs/documentation |
| ArkTS语法参考 | docs.openharmony.cn |
| 华为开发者论坛 | bbs.huawei.com |


先把这些网站收藏。用的时候随时查。

---

**相关文章：**

- 《程序员为什么必须关注鸿蒙开发》
- 《ArkTS核心语法详解》