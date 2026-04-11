"""
小红书数据平台 Web 服务
支持：Cookie配置、笔记爬取、评论获取、数据展示
"""
import os
import json
import re
import urllib
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# 添加父目录到路径，以便导入爬虫模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入爬虫模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init as init_paths


# 全局变量
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

COOKIE_FILE = DATA_DIR / "cookie.txt"

# 初始化爬虫
xhs_apis = XHS_Apis()


# ==================== 数据模型 ====================
class NoteInfo(BaseModel):
    """笔记信息"""
    note_id: str
    title: str
    desc: str
    user_nickname: str
    user_id: str
    liked_count: int
    collected_count: int
    commented_count: int
    shared_count: int
    cover: str
    images: List[str]
    video: Optional[str] = None
    tags: List[str]
    time: str
    url: str = ""


class CommentInfo(BaseModel):
    """评论信息"""
    comment_id: str
    content: str
    user_nickname: str
    user_id: str
    liked_count: int
    create_time: str
    sub_comments: List[dict] = []


# ==================== 工具函数 ====================
def save_cookie(cookie: str):
    """保存 Cookie 到文件"""
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write(cookie)


def load_cookie() -> Optional[str]:
    """加载 Cookie"""
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def get_note_id_from_url(url: str) -> tuple:
    """从URL提取笔记ID和xsec_token"""
    try:
        url_parse = urllib.parse.urlparse(url)
        note_id = url_parse.path.split("/")[-1]
        kvs = url_parse.query.split('&')
        kv_dist = {kv.split('=')[0]: kv.split('=')[1] for kv in kvs}
        xsec_token = kv_dist.get('xsec_token', '')
        return note_id, xsec_token
    except Exception as e:
        return None, None


def parse_note_info(raw_data: dict) -> Optional[dict]:
    """解析笔记原始数据"""
    try:
        # 实际 API 返回: data.items[0].note_card
        data = raw_data.get('data', {})
        items = data.get('items', [])
        if items:
            note_card = items[0].get('note_card', {})
        else:
            note_card = raw_data.get('noteCard', {})
        
        # 处理图片
        images = []
        image_list = note_card.get('image_list', [])
        for img in image_list:
            if 'url_default' in img:
                images.append(img['url_default'])
            elif 'url' in img:
                images.append(img['url'])
            elif 'url_pre' in img:
                images.append(img['url_pre'])
        
        # 处理视频
        video_url = None
        if note_card.get('type') == 'video':
            video_info = note_card.get('video', {})
            video_url = video_info.get('url', '')
        
        # 处理标签
        tags = []
        for tag in note_card.get('tag_list', []):
            if 'name' in tag:
                tags.append(tag['name'])
        
        # 处理互动数据
        interact = note_card.get('interact_info', {})
        liked_count = interact.get('liked_count', '0')
        collected_count = interact.get('collected_count', '0')
        comment_count = interact.get('comment_count', '0')
        shared_count = interact.get('share_count', '0')
        
        # 处理用户
        user = note_card.get('user', {})
        
        return {
            'note_id': note_card.get('note_id', ''),
            'title': note_card.get('display_title', '') or note_card.get('title', ''),
            'desc': note_card.get('desc', ''),
            'user_nickname': user.get('nick_name', '') or user.get('nickname', ''),
            'user_id': user.get('user_id', '') or user.get('userId', ''),
            'liked_count': int(liked_count) if str(liked_count).isdigit() else liked_count,
            'collected_count': int(collected_count) if str(collected_count).isdigit() else collected_count,
            'commented_count': int(comment_count) if str(comment_count).isdigit() else comment_count,
            'shared_count': int(shared_count) if str(shared_count).isdigit() else shared_count,
            'cover': note_card.get('cover', {}).get('url_default', ''),
            'images': images,
            'video': video_url,
            'tags': tags,
            'time': note_card.get('time', ''),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"解析笔记信息失败: {e}")
        return None


def parse_comment(raw_comments: List[dict]) -> List[dict]:
    """解析评论数据（适配新 API 字段名）"""
    comments = []
    for comment in raw_comments:
        # 处理一级评论
        user_info = comment.get('user_info', {}) or comment.get('userInfo', {})
        sub_comments_raw = comment.get('sub_comments', []) or comment.get('subComments', [])
        
        # 解析二级评论
        sub_comments = []
        for sub in sub_comments_raw:
            sub_user = sub.get('user_info', {}) or sub.get('userInfo', {})
            sub_comments.append({
                'comment_id': sub.get('id', ''),
                'content': sub.get('content', ''),
                'user_nickname': sub_user.get('nick_name', '') or sub_user.get('nickname', ''),
                'user_id': sub_user.get('user_id', '') or sub_user.get('userId', ''),
                'liked_count': sub.get('like_count', 0) or sub.get('likedCount', 0),
                'create_time': sub.get('create_time', '') or sub.get('createTime', ''),
            })
        
        comments.append({
            'comment_id': comment.get('id', ''),
            'content': comment.get('content', ''),
            'user_nickname': user_info.get('nick_name', '') or user_info.get('nickname', ''),
            'user_id': user_info.get('user_id', '') or user_info.get('userId', ''),
            'liked_count': comment.get('like_count', 0) or comment.get('likedCount', 0),
            'create_time': comment.get('create_time', '') or comment.get('createTime', ''),
            'sub_comments': sub_comments
        })
    return comments


# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="小红书数据平台",
    description="支持Cookie配置、笔记爬取、评论获取、数据展示",
    version="1.0.0"
)

# 静态文件和模板
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home():
    """首页"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>小红书数据平台</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header {
                text-align: center;
                color: white;
                padding: 40px 0;
            }
            .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
            .header p { opacity: 0.9; }
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .card {
                background: white;
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }
            .card:hover { transform: translateY(-5px); }
            .card-icon { font-size: 3rem; margin-bottom: 15px; }
            .card h3 { color: #333; margin-bottom: 10px; }
            .card p { color: #666; font-size: 0.9rem; line-height: 1.6; }
            .card a {
                display: inline-block;
                margin-top: 15px;
                padding: 10px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
            }
            .card a:hover { opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📕 小红书数据平台</h1>
                <p>支持 Cookie 配置、笔记爬取、评论获取、数据展示</p>
            </div>
            <div class="cards">
                <div class="card">
                    <div class="card-icon">🔑</div>
                    <h3>Cookie 配置</h3>
                    <p>配置你的小红书 Cookie，这是爬取数据的必要凭证。</p>
                    <a href="/config">前往配置 →</a>
                </div>
                <div class="card">
                    <div class="card-icon">📝</div>
                    <h3>笔记爬取</h3>
                    <p>输入笔记链接，快速获取笔记信息、标题、内容、作者等。</p>
                    <a href="/note">开始爬取 →</a>
                </div>
                <div class="card">
                    <div class="card-icon">💬</div>
                    <h3>评论获取</h3>
                    <p>获取任意笔记的全部评论，支持一级和二级评论。</p>
                    <a href="/comments">获取评论 →</a>
                </div>
                <div class="card">
                    <div class="card-icon">🔍</div>
                    <h3>笔记搜索</h3>
                    <p>通过关键词搜索笔记，支持多种筛选和排序方式。</p>
                    <a href="/search">开始搜索 →</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Cookie 配置页面"""
    cookie = load_cookie()
    has_cookie = cookie is not None and len(cookie) > 0
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "has_cookie": has_cookie,
        "cookie_preview": cookie[:50] + "..." if cookie and len(cookie) > 50 else cookie
    })


@app.post("/config/save")
async def save_config(cookie: str = Form(...)):
    """保存 Cookie"""
    if not cookie or len(cookie) < 10:
        raise HTTPException(status_code=400, detail="Cookie 无效")
    
    save_cookie(cookie)
    return {"success": True, "message": "Cookie 保存成功"}


@app.get("/note", response_class=HTMLResponse)
async def note_page(request: Request):
    """笔记爬取页面"""
    cookie = load_cookie()
    if not cookie:
        return RedirectResponse(url="/config?next=/note")
    return templates.TemplateResponse("note.html", {"request": request})


@app.post("/api/note")
async def scrape_note(note_url: str = Form(...)):
    """爬取单个笔记"""
    cookie = load_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置 Cookie")
    
    try:
        success, msg, note_info = xhs_apis.get_note_info(note_url, cookie)
        if not success:
            return {"success": False, "error": msg}
        
        # 解析数据
        parsed = parse_note_info(note_info)
        if parsed:
            parsed['url'] = note_url
            return {"success": True, "data": parsed}
        else:
            return {"success": False, "error": f"解析数据失败: {msg}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/comments", response_class=HTMLResponse)
async def comments_page(request: Request):
    """评论获取页面"""
    cookie = load_cookie()
    if not cookie:
        return RedirectResponse(url="/config?next=/comments")
    return templates.TemplateResponse("comments.html", {"request": request})


@app.post("/api/comments")
async def scrape_comments(note_url: str = Form(...)):
    """获取笔记评论"""
    cookie = load_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置 Cookie")
    
    try:
        success, msg, comments = xhs_apis.get_note_all_comment(note_url, cookie)
        if not success:
            return {"success": False, "error": msg}
        
        parsed_comments = parse_comment(comments)
        return {"success": True, "data": parsed_comments, "count": len(parsed_comments)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """搜索页面"""
    cookie = load_cookie()
    if not cookie:
        return RedirectResponse(url="/config?next=/search")
    return templates.TemplateResponse("search.html", {"request": request})


@app.post("/api/search")
async def search_notes(
    keyword: str = Form(...),
    num: int = Form(10),
    sort_type: int = Form(0),
    note_type: int = Form(0),
    note_time: int = Form(0)
):
    """搜索笔记"""
    cookie = load_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置 Cookie")
    
    try:
        success, msg, notes = xhs_apis.search_some_note(
            keyword, num, cookie, sort_type, note_type, note_time
        )
        if not success:
            return {"success": False, "error": msg}
        
        # 简化返回数据（适配新的 items 结构）
        simplified = []
        for note in notes[:num]:
            # 新 API 返回格式: {id, model_type, note_card: {...}}
            # 兼容旧格式: {id, title, desc, user: {...}}
            if 'note_card' in note:
                nc = note['note_card']
                interact = nc.get('interact_info', {})
                user = nc.get('user', {})
                images = nc.get('image_list', [])
                cover = ''
                for img in images:
                    cover = img.get('url_default', '') or img.get('url_pre', '') or cover
                    if cover:
                        break
                simplified.append({
                    'id': note.get('id', ''),
                    'title': nc.get('display_title', '') or nc.get('title', ''),
                    'desc': nc.get('desc', '')[:100] if nc.get('desc') else '',
                    'nickname': user.get('nick_name', '') or user.get('nickname', ''),
                    'liked_count': interact.get('liked_count', '0'),
                    'collected_count': interact.get('collected_count', '0'),
                    'comment_count': interact.get('comment_count', '0'),
                    'type': nc.get('type', 'normal'),
                    'cover': cover,
                    'time': nc.get('time', ''),
                })
            else:
                simplified.append({
                    'id': note.get('id', ''),
                    'title': note.get('display_title', '') or note.get('title', ''),
                    'desc': note.get('desc', '')[:100] if note.get('desc') else '',
                    'nickname': note.get('user', {}).get('nick_name', '') or note.get('user', {}).get('nickname', ''),
                    'liked_count': note.get('interact_info', {}).get('liked_count', 0),
                    'collected_count': note.get('interact_info', {}).get('collected_count', 0),
                    'comment_count': note.get('interact_info', {}).get('comment_count', 0),
                    'type': note.get('type', 'normal'),
                    'cover': note.get('cover', {}).get('url_default', '') or note.get('cover', {}).get('urlDefault', ''),
                    'time': note.get('time', ''),
                })
        
        return {"success": True, "data": simplified, "count": len(simplified)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/user", response_class=HTMLResponse)
async def user_page(request: Request):
    """用户信息页面"""
    cookie = load_cookie()
    if not cookie:
        return RedirectResponse(url="/config?next=/user")
    return templates.TemplateResponse("user.html", {"request": request})


@app.post("/api/user")
async def get_user_info(user_url: str = Form(...)):
    """获取用户信息"""
    cookie = load_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置 Cookie")
    
    try:
        url_parse = urllib.parse.urlparse(user_url)
        user_id = url_parse.path.split("/")[-1]
        
        success, msg, user_info = xhs_apis.get_user_info(user_id, cookie)
        if not success:
            return {"success": False, "error": msg}
        
        basic = user_info.get('data', {}).get('basicInfo', {})
        return {
            "success": True,
            "data": {
                'nickname': basic.get('nickname', ''),
                'avatar': basic.get('imageb', ''),
                'desc': basic.get('desc', ''),
                'liked_count': basic.get('likedCount', 0),
                'fans_count': basic.get('fans', 0),
                'follow_count': basic.get('follow', 0),
                'collected_count': basic.get('collectedCount', 0),
                '红薯等级': basic.get('level', {}).get('name', ''),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/status")
async def check_status():
    """检查服务状态"""
    cookie = load_cookie()
    return {
        "status": "running",
        "has_cookie": cookie is not None and len(cookie) > 0
    }


def generate_markdown(note_data: dict, comments: list) -> str:
    """生成 Markdown 格式的笔记导出内容（优化版，适合 LLM 分析）"""
    import datetime
    lines = []
    
    # ========== LLM 分析提示 ==========
    lines.append("# 📊 小红书笔记评论分析报告")
    lines.append("")
    lines.append("> **🤖 AI 分析提示**：请分析以下笔记的评论区，从普通用户视角提取有价值的信息，帮助用户：")
    lines.append("> - 识别真实用户体验 vs 营销/托")
    lines.append("> - 发现常见问题和踩坑点")
    lines.append("> - 提取实用的经验和技巧")
    lines.append("> - 判断笔记内容的可信度")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # ========== 笔记基础信息 ==========
    lines.append("## 📝 笔记信息")
    lines.append("")
    lines.append(f"| 字段 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 标题 | {note_data.get('title', 'N/A')} |")
    lines.append(f"| 作者 | {note_data.get('user_nickname', 'N/A')} |")
    lines.append(f"| 发布时间 | {note_data.get('create_time', 'N/A')} |")
    lines.append(f"| 笔记链接 | {note_data.get('url', 'N/A')} |")
    lines.append("")
    
    # ========== 互动数据 ==========
    lines.append("## 📈 互动数据")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 👍 点赞 | {note_data.get('liked_count', 0)} |")
    lines.append(f"| ⭐ 收藏 | {note_data.get('collected_count', 0)} |")
    lines.append(f"| 💬 评论 | {len(comments)} |")
    lines.append("")
    
    # 计算互动率
    likes = int(note_data.get('liked_count', 0) or 0)
    collects = int(note_data.get('collected_count', 0) or 0)
    comment_count = len(comments)
    if likes > 0:
        ratio = (collects / likes * 100)
        lines.append(f"> **📌 收藏率**: {ratio:.1f}% （收藏/点赞）")
        lines.append(f"> - 高收藏率(>50%)通常表示内容干货多、实用性强")
        lines.append(f"> - 低收藏率(<20%)可能偏娱乐或争议性内容")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # ========== 笔记正文 ==========
    lines.append("## 📄 笔记正文")
    lines.append("")
    desc = note_data.get('desc', '')
    if desc:
        lines.append(desc)
    else:
        lines.append("（无正文内容）")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # ========== 评论数据（按点赞排序） ==========
    lines.append("## 💬 评论数据")
    lines.append("")
    
    if not comments:
        lines.append("（暂无评论）")
    else:
        # 按点赞数排序，方便 LLM 快速识别热门观点
        sorted_comments = sorted(comments, key=lambda x: int(x.get('liked_count', 0) or 0), reverse=True)
        
        lines.append(f"**📊 共 {len(comments)} 条一级评论**（按点赞数从高到低排列）")
        lines.append("")
        
        for idx, comment in enumerate(sorted_comments, 1):
            likes_count = int(comment.get('liked_count', 0) or 0)
            sub_comments = comment.get('sub_comments', []) or []
            
            # 高赞评论标记
            hot_tag = "🔥" if likes_count >= 10 else ("⭐" if likes_count >= 5 else "")
            
            lines.append(f"### {hot_tag} 评论 #{idx} | 👍{likes_count} 赞")
            lines.append("")
            lines.append(f"**用户**: {comment.get('user_nickname', 'N/A')} | **时间**: {comment.get('create_time', 'N/A')}")
            lines.append("")
            lines.append(f"**内容**:")
            lines.append(f"{comment.get('content', '')}")
            lines.append("")
            
            # 二级评论
            if sub_comments:
                lines.append(f"> 💬 {len(sub_comments)} 条回复")
                lines.append("")
                for sub_idx, sub in enumerate(sub_comments[:5], 1):  # 最多显示5条回复
                    sub_likes = int(sub.get('liked_count', 0) or 0)
                    sub_hot = "🔥" if sub_likes >= 5 else ""
                    lines.append(f"> - {sub.get('user_nickname', '用户')} ({sub_likes}赞): {sub.get('content', '')[:100]}")
                if len(sub_comments) > 5:
                    lines.append(f"> - ... 还有 {len(sub_comments) - 5} 条回复未显示")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    # ========== LLM 分析引导 ==========
    lines.append("## 🔍 AI 分析任务")
    lines.append("")
    lines.append("请根据以上内容，完成以下分析：")
    lines.append("")
    lines.append("### 1️⃣ 舆情概览")
    lines.append("- 评论区整体情绪是正面、中立还是负面？")
    lines.append("- 用户对笔记内容的评价如何？")
    lines.append("")
    lines.append("### 2️⃣ 踩坑预警 ⚠️")
    lines.append("- 找出用户提到的常见问题、负面体验、后悔购买等")
    lines.append("- 识别可能的托或营销号特征")
    lines.append("")
    lines.append("### 3️⃣ 实用经验 💡")
    lines.append("- 提取用户分享的真实经验、使用技巧、注意事项")
    lines.append("- 记录高质量的补充信息")
    lines.append("")
    lines.append("### 4️⃣ 可信度评估")
    lines.append("- 根据点赞/收藏比判断内容质量")
    lines.append("- 根据评论内容判断作者是否可信")
    lines.append("")
    lines.append("### 5️⃣ 总结建议")
    lines.append("- 用简洁的语言总结：这个笔记值不值得参考？")
    lines.append("- 给读者最重要的 3 条建议")
    lines.append("")
    
    lines.append("---")
    lines.append(f"*导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("*📋 格式优化版 - 适合 AI 大模型分析使用*")
    
    return "\n".join(lines)


@app.post("/api/export/markdown")
async def export_markdown(note_url: str = Form(...)):
    """导出笔记和评论为 Markdown 文件"""
    cookie = load_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置 Cookie")
    
    try:
        # 获取笔记详情
        success, msg, note_info = xhs_apis.get_note_info(note_url, cookie)
        if not success:
            return {"success": False, "error": msg}
        
        note_data = parse_note_info(note_info)
        if not note_data:
            return {"success": False, "error": "解析笔记数据失败"}
        
        note_data['url'] = note_url
        
        # 获取评论
        success, msg, comments = xhs_apis.get_note_all_comment(note_url, cookie)
        if not success:
            return {"success": False, "error": msg}
        
        parsed_comments = parse_comment(comments)
        
        # 生成 Markdown
        markdown_content = generate_markdown(note_data, parsed_comments)
        
        # 生成文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', note_data.get('title', '未命名'))[:30]
        note_id = note_data.get('note_id', 'unknown')
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"小红书_{safe_title}_{note_id}_{timestamp}.md"
        
        # 返回文件下载
        from fastapi.responses import StreamingResponse
        from io import BytesIO
        
        buffer = BytesIO(markdown_content.encode('utf-8'))
        
        # URL编码文件名，解决中文文件名问题
        safe_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            buffer,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ==================== 启动 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 小红书数据平台 Web 服务")
    print("=" * 50)
    print("📍 访问地址: http://localhost:8080")
    print("📝 功能页面:")
    print("   - 首页:     /")
    print("   - 配置:     /config")
    print("   - 笔记爬取: /note")
    print("   - 评论获取: /comments")
    print("   - 笔记搜索: /search")
    print("   - 用户信息: /user")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
