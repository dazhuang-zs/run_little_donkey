# 小红书评论洞察 - 快速使用指南

## 项目优化完成！

已完成以下优化：

✅ **爬虫优化**
- 支持获取子评论（用户之间的互相回复）
- 随机延迟防爬
- 指数退避重试机制
- User-Agent 池
- 代理支持

✅ **LLM 集成**
- 支持 OpenAI、Claude、通义千问
- Mock 模式用于测试
- 智能评论过滤和排序

✅ **文档完善**
- 优化方案文档
- 快速使用指南

---

## 一、环境准备

### 1. 安装依赖

```bash
cd /Users/xiaoyuer/cursor-projects/run_little_donkey/comment-insight/backend
pip install -r requirements.txt
```

### 2. 获取小红书 Cookie

1. 浏览器打开 https://www.xiaohongshu.com 并登录
2. 按 F12 打开开发者工具
3. 点击 **Application** 标签
4. 左侧选择 **Cookies** → **https://www.xiaohongshu.com**
5. 找到以下 Cookie 并复制：
   - `a1`（最重要）
   - `webId`
   - `web_session`（如果有）

6. 将 Cookie 组合成字符串，例如：
   ```
   a1=18ce3dxxxxxx; webId=xxxxxx; web_session=xxxxxx
   ```

---

## 二、快速测试

### 测试 1: 爬虫单独测试

创建一个测试文件 `test_scraper.py`：

```python
import sys
sys.path.insert(0, '/Users/xiaoyuer/cursor-projects/run_little_donkey/comment-insight/backend')

from app.scraper_optimized import XiaohongshuScraperOptimized

# 初始化爬虫
scraper = XiaohongshuScraperOptimized(
    cookies="你的Cookie字符串",  # 替换为你的 Cookie
    use_random_delay=True,
    min_delay=2.0,
    max_delay=5.0,
    max_retries=3
)

# 获取笔记 ID 示例：
# 小红书链接：https://www.xiaohongshu.com/explore/64b8c3d2000000001f003abc
# 笔记 ID 就是：64b8c3d2000000001f003abc

note_id = "你的笔记ID"  # 替换为真实的笔记 ID

# 获取所有评论（包含子评论）
print(f"开始获取笔记 {note_id} 的评论...")
comments = scraper.get_all_comments_with_sub(
    note_id=note_id,
    max_pages=3,  # 先试试 3 页
    include_sub_comments=True
)

# 导出到 JSON 文件
scraper.export_comments_to_json(comments, "comments.json")

print(f"\n成功获取 {len(comments)} 条主评论！")
```

### 测试 2: LLM 分析测试

创建 `test_analyzer.py`：

```python
import sys
sys.path.insert(0, '/Users/xiaoyuer/cursor-projects/run_little_donkey/comment-insight/backend')

from app.analyzer import CommentAnalyzer
import json

# 加载刚才导出的评论
with open("comments.json", "r", encoding="utf-8") as f:
    comments = json.load(f)

# 初始化分析器（先使用 mock 模式测试）
analyzer = CommentAnalyzer(
    provider="mock"  # 先用 mock，没问题再换真实 LLM
)

# 如果要用真实的 OpenAI：
# analyzer = CommentAnalyzer(
#     provider="openai",
#     api_key="sk-xxxxxx",
#     model="gpt-3.5-turbo",
#     base_url="https://api.openai.com/v1"  # 或你的代理地址
# )

# 分析评论
print("开始分析评论...")
result = analyzer.analyze(comments)

# 输出结果
print("\n" + "="*60)
print("【有用总结】")
for item in result.summary:
    print(f"✅ {item}")

print("\n【避坑指南】")
for item in result.pitfalls:
    print(f"⚠️ {item}")

print("\n【待确认】")
for item in result.uncertain:
    print(f"❓ {item}")
print("="*60)
```

---

## 三、启动 Web 服务

```bash
cd /Users/xiaoyuer/cursor-projects/run_little_donkey/comment-insight/backend
python -m app.main
```

然后打开浏览器访问：http://localhost:8000

---

## 四、常见问题

### Q: Cookie 有效期多久？
A: 通常 1-2 周，如果提示登录失效，重新获取 Cookie 即可。

### Q: 如何获取笔记 ID？
A: 从链接中提取，例如：
- `https://www.xiaohongshu.com/explore/64b8c3d2000000001f003abc`
- 笔记 ID 就是 `64b8c3d2000000001f003abc`

### Q: 被限流了怎么办？
A: 
1. 增加 `min_delay` 和 `max_delay` 的值
2. 减少 `max_pages`
3. 使用代理
4. 换一个账号的 Cookie

### Q: 支持哪些 LLM？
A: 
- OpenAI (GPT-3.5/4)
- Claude (Haiku/Sonnet/Opus)
- 通义千问 (Qwen)
- Mock 模式（测试用）

---

## 五、文件说明

| 文件 | 说明 |
|------|------|
| `app/scraper_optimized.py` | 优化后的爬虫（推荐使用） |
| `app/scraper.py` | 原始爬虫 |
| `app/analyzer.py` | LLM 评论分析模块 |
| `app/parser.py` | 链接解析模块 |
| `app/main.py` | FastAPI 后端 |
| `OPTIMIZATION.md` | 详细优化方案 |
| `QUICKSTART.md` | 本文件 |

---

## 六、下一步

1. ✅ 获取 Cookie 并测试爬虫
2. ✅ 导出评论到 JSON
3. ✅ 测试 LLM 分析（先用 mock）
4. ✅ 配置真实的 LLM API Key
5. ✅ 启动 Web 服务

祝你使用愉快！如有问题请参考 OPTIMIZATION.md
