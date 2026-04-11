"""
小红书评论爬虫模块
使用登录态调用 API
"""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime


class XiaohongshuScraper:
    """小红书评论爬虫"""
    
    def __init__(self, cookies: str = None):
        """
        初始化爬虫
        
        Args:
            cookies: 小红书登录 Cookie（可选，后续用户提供）
        """
        self.cookies = cookies or ""
        self.base_url = "https://edith.xiaohongshu.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com"
        }
        if self.cookies:
            self.headers["Cookie"] = self.cookies
    
    def set_cookies(self, cookies: str):
        """设置 Cookie"""
        self.cookies = cookies
        self.headers["Cookie"] = cookies
    
    def get_note_info(self, note_id: str) -> Dict:
        """
        获取笔记基本信息
        
        Args:
            note_id: 笔记 ID
            
        Returns:
            笔记信息字典
        """
        url = f"{self.base_url}/api/sns/web/v1/feed"
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": "1"}
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取笔记失败: {response.status_code}")
                return {}
        except Exception as e:
            print(f"请求异常: {e}")
            return {}
    
    def get_comments(self, note_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取笔记评论
        
        Args:
            note_id: 笔记 ID
            page: 页码（从 1 开始）
            page_size: 每页数量（建议 20）
            
        Returns:
            {
                "comments": [...],  # 评论列表
                "has_more": True/False,  # 是否有更多
                "total": 100,  # 总数（如果有）
                "page_size": 20,  # 实际每页数量
                "cursor": "xxx"  # 下页游标（用于分页）
            }
        """
        url = f"{self.base_url}/api/sns/web/v1/comment/page"
        data = {
            "note_id": note_id,
            "cursor": "",
            "top_comment_id": "",
            "image_formats": ["jpg", "webp", "avif"],
            "page_size": page_size,
            "type": "comment"
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return self._parse_comment_response(result)
            else:
                print(f"获取评论失败: {response.status_code}, {response.text}")
                return {"comments": [], "has_more": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"请求异常: {e}")
            return {"comments": [], "has_more": False, "error": str(e)}
    
    def _parse_comment_response(self, response: Dict) -> Dict:
        """解析评论响应"""
        try:
            data = response.get("data", {})
            comments = data.get("comments", [])
            
            # 提取评论信息
            parsed_comments = []
            for comment in comments:
                parsed = {
                    "id": comment.get("comment", {}).get("id", ""),
                    "content": comment.get("comment", {}).get("content", ""),
                    "user_name": comment.get("comment", {}).get("user", {}).get("nickname", ""),
                    "user_id": comment.get("comment", {}).get("user", {}).get("user_id", ""),
                    "create_time": comment.get("comment", {}).get("create_time", ""),
                    "liked_count": comment.get("comment", {}).get("liked_count", 0),
                    "reply_count": comment.get("comment", {}).get("reply_count", 0),
                }
                parsed_comments.append(parsed)
            
            # 检查是否有更多
            has_more = data.get("has_more", False)
            cursor = data.get("cursor", "")
            
            return {
                "comments": parsed_comments,
                "has_more": has_more,
                "cursor": cursor,
                "total": data.get("total", len(parsed_comments)),
                "page_size": len(parsed_comments)
            }
        except Exception as e:
            print(f"解析响应失败: {e}")
            return {"comments": [], "has_more": False, "error": str(e)}
    
    def get_all_comments(self, note_id: str, max_pages: int = 5) -> List[Dict]:
        """
        获取所有评论（带分页）
        
        Args:
            note_id: 笔记 ID
            max_pages: 最大页数限制
            
        Returns:
            所有评论列表
        """
        all_comments = []
        cursor = ""
        
        for page in range(1, max_pages + 1):
            print(f"获取第 {page} 页...")
            
            url = f"{self.base_url}/api/sns/web/v1/comment/page"
            data = {
                "note_id": note_id,
                "cursor": cursor,
                "top_comment_id": "",
                "image_formats": ["jpg", "webp", "avif"],
                "page_size": 20,
                "type": "comment"
            }
            
            try:
                response = requests.post(url, json=data, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    print(f"第 {page} 页请求失败")
                    break
                    
                result = response.json()
                parsed = self._parse_comment_response(result)
                
                all_comments.extend(parsed["comments"])
                cursor = parsed.get("cursor", "")
                
                if not parsed["has_more"]:
                    print(f"第 {page} 页是最后一页")
                    break
                
                # 间隔 3 秒，避免频繁请求
                time.sleep(3)
                
            except Exception as e:
                print(f"第 {page} 页异常: {e}")
                break
        
        print(f"共获取 {len(all_comments)} 条评论")
        return all_comments


def test_with_cookie():
    """测试函数（需要 Cookie）"""
    scraper = XiaohongshuScraper()
    
    # TODO: 替换为你的 Cookie
    # Cookie 获取方式：浏览器登录小红书 → F12 → Application → Cookies → xiaohongshu.com
    # cookie_str = "a1=xxx; webId=xxx; ..." 
    # scraper.set_cookies(cookie_str)
    
    # TODO: 替换为测试的笔记 ID
    # note_id = "1234567890abcdef"
    # comments = scraper.get_all_comments(note_id, max_pages=2)
    # print(comments)
    
    print("请设置 Cookie 后测试")


if __name__ == "__main__":
    test_with_cookie()