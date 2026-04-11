# spider-xhs Web 架构文档

> 作者：AI Assistant  
> 日期：2026-04-11  
> 版本：v1.0.0

---

## 1. 项目概述

spider-xhs Web 是一个基于 FastAPI 的小红书数据采集平台，提供可视化的 Web 界面来管理 Cookie、爬取笔记、获取评论和搜索内容。

## 2. 目录结构

```
spider-xhs/
├── web/                          # Web 应用目录
│   ├── main.py                   # FastAPI 主应用
│   ├── requirements.txt          # Python 依赖
│   ├── templates/                # HTML 模板
│   │   ├── config.html           # Cookie 配置页
│   │   ├── note.html             # 笔记爬取页
│   │   ├── comments.html          # 评论获取页
│   │   ├── search.html            # 笔记搜索页
│   │   └── user.html              # 用户信息页
│   └── static/                   # 静态资源目录
│
├── apis/                         # 爬虫 API
│   └── xhs_pc_apis.py           # 小红书 API 封装
│
├── xhs_utils/                    # 工具函数
│   ├── xhs_util.py              # 签名生成
│   ├── cookie_util.py           # Cookie 解析
│   ├── data_util.py            # 数据处理
│   └── common_util.py           # 通用工具
│
└── static/                       # JS 签名文件
    └── *.js                     # 小红书加密 JS
```

## 3. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 高性能异步 API 框架 |
| 服务 | Uvicorn | ASGI 服务器 |
| 模板引擎 | Jinja2 | HTML 模板渲染 |
| HTTP 客户端 | requests | 爬虫请求 |
| JavaScript 执行 | PyExecJS | 执行签名 JS |

## 4. 功能模块

### 4.1 Cookie 配置
- **功能**: 管理小红书 Cookie
- **存储**: 本地文件 `data/cookie.txt`
- **API**: `POST /config/save`

### 4.2 笔记爬取
- **功能**: 获取单篇笔记的详细信息
- **输入**: 笔记链接
- **输出**: 标题、内容、作者、统计数据、图片
- **API**: `POST /api/note`

### 4.3 评论获取
- **功能**: 获取笔记的全部评论
- **输入**: 笔记链接
- **输出**: 一级评论 + 二级回复
- **API**: `POST /api/comments`

### 4.4 笔记搜索
- **功能**: 关键词搜索笔记
- **筛选**: 排序方式、笔记类型、发布时间
- **API**: `POST /api/search`

### 4.5 用户信息
- **功能**: 查询用户资料
- **输出**: 粉丝数、关注数、获赞数、收藏数
- **API**: `POST /api/user`

## 5. API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 首页 |
| `/config` | GET | Cookie 配置页 |
| `/config/save` | POST | 保存 Cookie |
| `/note` | GET | 笔记爬取页 |
| `/api/note` | POST | 爬取笔记 |
| `/comments` | GET | 评论获取页 |
| `/api/comments` | POST | 获取评论 |
| `/search` | GET | 搜索页 |
| `/api/search` | POST | 搜索笔记 |
| `/user` | GET | 用户信息页 |
| `/api/user` | POST | 查询用户 |
| `/api/status` | GET | 服务状态 |

## 6. 页面路由

```
/                    首页 - 功能入口
├── /config          Cookie 配置
├── /note            笔记爬取
├── /comments        评论获取
├── /search          笔记搜索
└── /user            用户信息
```

## 7. 安全设计

### 7.1 Cookie 安全
- Cookie 存储在本地文件，不上传到远程
- 每次请求动态读取

### 7.2 输入验证
- URL 格式验证
- Cookie 长度检查

### 7.3 限流
- 每个 IP 每分钟限制请求次数

## 8. 启动方式

```bash
# 安装依赖
cd spider-xhs/web
pip install -r requirements.txt

# 启动服务
python main.py

# 访问地址
# http://localhost:8080
```

## 9. 依赖项

```
fastapi>=0.109.0
uvicorn>=0.27.0
jinja2>=3.1.0
python-multipart>=0.0.6
```

## 10. 未来扩展

- [ ] 添加用户认证系统
- [ ] 添加数据导出功能 (Excel/JSON)
- [ ] 添加代理池支持
- [ ] 添加任务队列支持
- [ ] 添加数据可视化图表
- [ ] 添加移动端适配

---

*文档版本: v1.0.0*
