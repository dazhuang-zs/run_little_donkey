"""
评论洞察助手 - MVP 后端
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import re

# 导入爬虫模块
from app.scraper import XiaohongshuScraper

app = FastAPI(title="评论洞察助手", version="1.0.0")

# 配置静态文件和模板
templates = Jinja2Templates(directory="templates")

# 全局爬虫实例（后续可改为依赖注入）
scraper = XiaohongshuScraper()


class AnalyzeRequest(BaseModel):
    url: str


class ScraperTestRequest(BaseModel):
    note_id: str
    cookies: str = ""


def parse_url(url: str) -> Dict[str, str]:
    """解析分享链接，提取平台和内容ID"""
    
    # 小红书
    xiaohongshu_pattern = r'(?:www\.)?xiaohongshu\.com/explore/([a-zA-Z0-9]+)'
    match = re.search(xiaohongshu_pattern, url)
    if match:
        return {"platform": "xiaohongshu", "content_id": match.group(1)}
    
    # 小红书短链
    xiaohongshu_short = r'xhsc\.com/([a-zA-Z0-9]+)'
    match = re.search(xiaohongshu_short, url)
    if match:
        return {"platform": "xiaohongshu", "content_id": match.group(1)}
    
    # 大众点评
    dianping_pattern = r'dianping\.com/shop/([0-9]+)'
    match = re.search(dianping_pattern, url)
    if match:
        return {"platform": "dianping", "content_id": match.group(1)}
    
    # 抖音
    douyin_pattern = r'douyin\.com/([a-zA-Z0-9]+)'
    match = re.search(douyin_pattern, url)
    if match:
        return {"platform": "douyin", "content_id": match.group(1)}
    
    # 抖音短链
    douyin_short = r'v\.douyin\.com/([a-zA-Z0-9]+)'
    match = re.search(douyin_short, url)
    if match:
        return {"platform": "douyin", "content_id": match.group(1)}
    
    raise HTTPException(status_code=400, detail="无法识别的链接格式")


def analyze_comments_mock(platform: str, content_id: str) -> Dict[str, Any]:
    """模拟评论分析（MVP阶段使用模拟数据）"""
    
    mock_data = {
        "xiaohongshu": {
            "summary": [
                "✅ 产品性价比高，适合学生党",
                "✅ 包装精美，送礼自用都合适",
                "✅ 物流速度快，两天到货"
            ],
            "pitfalls": [
                "⚠️ 部分用户反馈实物与图片有色差",
                "⚠️ 客服响应较慢，需要等待",
                "⚠️ 量有点少，不适合多人分享"
            ],
            "uncertain": [
                "❓ 是否正品？建议先买小包装试试",
                "❓ 质保期多长时间？",
                "❓ 适合什么肤质？"
            ],
            "sentiment": {"positive": 65, "neutral": 25, "negative": 10}
        },
        "dianping": {
            "summary": [
                "✅ 菜品口味不错，推荐招牌菜",
                "✅ 服务态度好，服务员热情",
                "✅ 性价比高，团购很划算"
            ],
            "pitfalls": [
                "⚠️ 排队时间较长，建议提前预约",
                "⚠️ 环境有点嘈杂，适合朋友聚餐",
                "⚠️ 上菜速度有点慢"
            ],
            "uncertain": [
                "❓ 停车方便吗？",
                "❓ 有没有包间？",
                "❓ 是否支持外卖？"
            ],
            "sentiment": {"positive": 70, "neutral": 20, "negative": 10}
        },
        "douyin": {
            "summary": [
                "✅ 视频内容真实，没有过度滤镜",
                "✅ 博主推荐的产品确实好用",
                "✅ 价格实惠，值得购买"
            ],
            "pitfalls": [
                "⚠️ 发货较慢，等了一周",
                "⚠️ 部分评论说质量一般",
                "⚠️ 售后处理较慢"
            ],
            "uncertain": [
                "❓ 和视频里是一样的吗？",
                "❓ 什么时候有优惠？",
                "❓ 有运费险吗？"
            ],
            "sentiment": {"positive": 60, "neutral": 30, "negative": 10}
        }
    }
    
    return mock_data.get(platform, mock_data["xiaohongshu"])


# 前端页面路由
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    """分析评论接口"""
    
    parsed = parse_url(request.url)
    result = analyze_comments_mock(parsed["platform"], parsed["content_id"])
    
    return {
        "platform": parsed["platform"],
        "content_id": parsed["content_id"],
        "url": request.url,
        "summary": result["summary"],
        "pitfalls": result["pitfalls"],
        "uncertain": result["uncertain"],
        "sentiment": result["sentiment"]
    }


@app.get("/api/platforms")
def get_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": [
            {"name": "xiaohongshu", "display": "小红书"},
            {"name": "dianping", "display": "大众点评"},
            {"name": "douyin", "display": "抖音"}
        ]
    }


@app.post("/api/test-scraper")
def test_scraper(request: ScraperTestRequest):
    """
    测试小红书爬虫 API
    用于获取真实评论数据
    """
    # 更新 Cookie
    if request.cookies:
        scraper.set_cookies(request.cookies)
    
    # 获取评论（先获取 1 页测试）
    result = scraper.get_comments(request.note_id, page=1, page_size=20)
    
    return {
        "note_id": request.note_id,
        "comments": result.get("comments", []),
        "has_more": result.get("has_more", False),
        "total": result.get("total", 0),
        "page_size": result.get("page_size", 0),
        "cursor": result.get("cursor", ""),
        "error": result.get("error", "")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)