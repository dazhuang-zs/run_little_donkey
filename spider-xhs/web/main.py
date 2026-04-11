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
        note_card = raw_data.get('noteCard', {})
        if not note_card:
            items = raw_data.get('items', [])
            if items and len(items) > 0:
                note_card = items[0].get('noteCard', {})
        
        user = note_card.get('user', {})
        
        # 处理图片
        images = []
        image_list = note_card.get('imageList', [])
        for img in image_list:
            if 'urlDefaultSize' in img:
                images.append(img['urlDefaultSize'])
            elif 'url' in img:
                images.append(img['url'])
        
        # 处理视频
        video_url = None
        if note_card.get('type') == 'video':
            video_info = note_card.get('video', {})
            video_url = video_info.get('url', '')
        
        # 处理标签
        tags = []
        for tag in note_card.get('tagList', []):
            if 'name' in tag:
                tags.append(tag['name'])
        
        return {
            'note_id': note_card.get('noteId', ''),
            'title': note_card.get('title', ''),
            'desc': note_card.get('desc', ''),
            'user_nickname': user.get('nickname', ''),
            'user_id': user.get('userId', ''),
            'liked_count': note_card.get('interactInfo', {}).get('likedCount', 0),
            'collected_count': note_card.get('interactInfo', {}).get('collectedCount', 0),
            'commented_count': note_card.get('interactInfo', {}).get('commentedCount', 0),
            'shared_count': note_card.get('interactInfo', {}).get('sharedCount', 0),
            'cover': note_card.get('cover', {}).get('urlDefault', ''),
            'images': images,
            'video': video_url,
            'tags': tags,
            'time': note_card.get('time', ''),
        }
    except Exception as e:
        print(f"解析笔记信息失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_comment(raw_comments: List[dict]) -> List[dict]:
    """解析评论数据"""
    comments = []
    for comment in raw_comments:
        sub_comments = []
        raw_subs = comment.get('subComments', [])
        for sub in raw_subs:
            sub_comments.append({
                'id': sub.get('id', ''),
                'content': sub.get('content', ''),
                'userInfo': {
                    'nickname': sub.get('userInfo', {}).get('nickname', ''),
                    'userId': sub.get('userInfo', {}).get('userId', '')
                },
                'likedCount': sub.get('likedCount', 0),
                'createTime': sub.get('createTime', '')
            })
        comments.append({
            'comment_id': comment.get('id', ''),
            'content': comment.get('content', ''),
            'user_nickname': comment.get('userInfo', {}).get('nickname', ''),
            'user_id': comment.get('userInfo', {}).get('userId', ''),
            'liked_count': comment.get('likedCount', 0),
            'create_time': comment.get('createTime', ''),
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
        
        # 简化返回数据
        simplified = []
        for note in notes[:num]:
            simplified.append({
                'id': note.get('id', ''),
                'title': note.get('displayTitle', '') or note.get('title', ''),
                'desc': note.get('desc', ''),
                'nickname': note.get('user', {}).get('nickname', ''),
                'liked_count': note.get('interactInfo', {}).get('likedCount', 0),
                'type': note.get('type', 'normal'),
                'cover': note.get('cover', {}).get('urlDefault', ''),
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


# ==================== 启动 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 小红书数据平台 Web 服务")
    print("=" * 50)
    print("📍 访问地址: http://localhost:8083")
    print("📝 功能页面:")
    print("   - 首页:     /")
    print("   - 配置:     /config")
    print("   - 笔记爬取: /note")
    print("   - 评论获取: /comments")
    print("   - 笔记搜索: /search")
    print("   - 用户信息: /user")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8083, reload=False)
