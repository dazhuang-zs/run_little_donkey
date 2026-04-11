"""
小红书评论爬虫 - 优化版
支持：
- 获取主评论 + 子评论（互相评论）
- 随机延迟防爬
- 指数退避重试
- User-Agent 池
- 代理支持
"""
import requests
import time
import random
import json
from typing import List, Dict, Optional
from datetime import datetime


class XiaohongshuScraperOptimized:
    """小红书评论爬虫 - 优化版"""
    
    # User-Agent 池
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    def __init__(
        self,
        cookies: str = None,
        use_random_delay: bool = True,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
        proxy: str = None
    ):
        """
        初始化爬虫
        
        Args:
            cookies: 小红书登录 Cookie
            use_random_delay: 是否使用随机延迟
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            max_retries: 最大重试次数
            proxy: 代理地址，如 http://127.0.0.1:7890
        """
        self.cookies = cookies or ""
        self.base_url = "https://edith.xiaohongshu.com"
        self.use_random_delay = use_random_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.proxy = proxy
        
        # 初始化请求头
        self._refresh_headers()
    
    def _refresh_headers(self):
        """刷新请求头（随机 User-Agent）"""
        self.headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
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
    
    def set_proxy(self, proxy: str):
        """设置代理"""
        self.proxy = proxy
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """随机延迟"""
        if not self.use_random_delay:
            return
        
        min_d = min_delay if min_delay is not None else self.min_delay
        max_d = max_delay if max_delay is not None else self.max_delay
        delay = random.uniform(min_d, max_d)
        print(f"等待 {delay:.1f} 秒...")
        time.sleep(delay)
    
    def _request_with_retry(
        self,
        url: str,
        method: str = "POST",
        json_data: Dict = None,
        timeout: int = 15
    ) -> Optional[Dict]:
        """
        带重试的请求
        
        Args:
            url: 请求URL
            method: 请求方法
            json_data: JSON数据
            timeout: 超时时间
            
        Returns:
            响应字典，失败返回None
        """
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        
        for retry in range(self.max_retries):
            try:
                if method.upper() == "POST":
                    response = requests.post(
                        url,
                        json=json_data,
                        headers=self.headers,
                        proxies=proxies,
                        timeout=timeout
                    )
                else:
                    response = requests.get(
                        url,
                        headers=self.headers,
                        proxies=proxies,
                        timeout=timeout
                    )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # 触发限流，等待更长时间
                    wait_time = (retry + 1) * 10
                    print(f"触发限流，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                else:
                    print(f"请求失败: {response.status_code}, {response.text[:200]}")
                    
            except Exception as e:
                print(f"请求异常 (重试 {retry + 1}/{self.max_retries}): {e}")
            
            # 指数退避重试
            if retry < self.max_retries - 1:
                wait_time = (2 ** retry) * 2
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                # 随机切换 UA
                self._refresh_headers()
        
        return None
    
    def get_note_info(self, note_id: str) -> Dict:
        """获取笔记基本信息"""
        url = f"{self.base_url}/api/sns/web/v1/feed"
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": "1"}
        }
        
        result = self._request_with_retry(url, "POST", data)
        return result if result else {}
    
    def get_comments(
        self,
        note_id: str,
        cursor: str = "",
        page_size: int = 20
    ) -> Dict:
        """
        获取一页主评论
        
        Args:
            note_id: 笔记 ID
            cursor: 分页游标
            page_size: 每页数量
            
        Returns:
            评论数据
        """
        url = f"{self.base_url}/api/sns/web/v1/comment/page"
        data = {
            "note_id": note_id,
            "cursor": cursor,
            "top_comment_id": "",
            "image_formats": ["jpg", "webp", "avif"],
            "page_size": page_size,
            "type": "comment"
        }
        
        result = self._request_with_retry(url, "POST", data)
        if result:
            return self._parse_comment_response(result)
        return {"comments": [], "has_more": False, "error": "请求失败"}
    
    def get_sub_comments(
        self,
        note_id: str,
        comment_id: str,
        cursor: str = "",
        page_size: int = 20
    ) -> Dict:
        """
        获取子评论（回复评论）
        
        Args:
            note_id: 笔记 ID
            comment_id: 主评论 ID
            cursor: 分页游标
            page_size: 每页数量
            
        Returns:
            子评论数据
        """
        url = f"{self.base_url}/api/sns/web/v1/comment/sub/page"
        data = {
            "note_id": note_id,
            "comment_id": comment_id,
            "cursor": cursor,
            "image_formats": ["jpg", "webp", "avif"],
            "page_size": page_size
        }
        
        result = self._request_with_retry(url, "POST", data)
        if result:
            return self._parse_sub_comment_response(result)
        return {"comments": [], "has_more": False, "error": "请求失败"}
    
    def _parse_comment_response(self, response: Dict) -> Dict:
        """解析主评论响应"""
        try:
            data = response.get("data", {})
            comments = data.get("comments", [])
            
            parsed_comments = []
            for comment in comments:
                comment_data = comment.get("comment", {})
                parsed = {
                    "id": comment_data.get("id", ""),
                    "content": comment_data.get("content", ""),
                    "user_name": comment_data.get("user", {}).get("nickname", ""),
                    "user_id": comment_data.get("user", {}).get("user_id", ""),
                    "create_time": comment_data.get("create_time", ""),
                    "liked_count": comment_data.get("liked_count", 0),
                    "reply_count": comment_data.get("reply_count", 0),
                    "sub_comments": []
                }
                parsed_comments.append(parsed)
            
            return {
                "comments": parsed_comments,
                "has_more": data.get("has_more", False),
                "cursor": data.get("cursor", ""),
                "total": data.get("total", len(parsed_comments))
            }
        except Exception as e:
            print(f"解析评论响应失败: {e}")
            return {"comments": [], "has_more": False, "error": str(e)}
    
    def _parse_sub_comment_response(self, response: Dict) -> Dict:
        """解析子评论响应"""
        try:
            data = response.get("data", {})
            comments = data.get("comments", [])
            
            parsed_comments = []
            for comment in comments:
                comment_data = comment.get("comment", {})
                target_comment = comment.get("target_comment", {})
                
                parsed = {
                    "id": comment_data.get("id", ""),
                    "content": comment_data.get("content", ""),
                    "user_name": comment_data.get("user", {}).get("nickname", ""),
                    "user_id": comment_data.get("user", {}).get("user_id", ""),
                    "target_user_name": target_comment.get("user", {}).get("nickname", ""),
                    "target_comment_id": target_comment.get("id", ""),
                    "create_time": comment_data.get("create_time", ""),
                    "liked_count": comment_data.get("liked_count", 0)
                }
                parsed_comments.append(parsed)
            
            return {
                "comments": parsed_comments,
                "has_more": data.get("has_more", False),
                "cursor": data.get("cursor", "")
            }
        except Exception as e:
            print(f"解析子评论响应失败: {e}")
            return {"comments": [], "has_more": False, "error": str(e)}
    
    def _get_all_sub_comments(self, note_id: str, comment_id: str) -> List[Dict]:
        """获取某条主评论的所有子评论"""
        all_sub_comments = []
        cursor = ""
        page = 1
        
        while True:
            print(f"  获取子评论第 {page} 页...")
            result = self.get_sub_comments(note_id, comment_id, cursor)
            
            if result.get("error"):
                print(f"  获取子评论失败: {result['error']}")
                break
            
            all_sub_comments.extend(result["comments"])
            
            if not result["has_more"]:
                print(f"  子评论获取完成，共 {len(all_sub_comments)} 条")
                break
            
            cursor = result.get("cursor", "")
            page += 1
            
            # 子评论间隔短一些
            self._random_delay(min_delay=1.0, max_delay=2.0)
        
        return all_sub_comments
    
    def get_all_comments_with_sub(
        self,
        note_id: str,
        max_pages: int = 10,
        include_sub_comments: bool = True
    ) -> List[Dict]:
        """
        获取所有评论（包含子评论）
        
        Args:
            note_id: 笔记 ID
            max_pages: 最大主评论页数
            include_sub_comments: 是否获取子评论
            
        Returns:
            评论列表，每条评论包含 sub_comments 字段
        """
        all_comments = []
        cursor = ""
        
        for page in range(1, max_pages + 1):
            print(f"获取主评论第 {page} 页...")
            
            result = self.get_comments(note_id, cursor)
            
            if result.get("error"):
                print(f"获取评论失败: {result['error']}")
                break
            
            comments = result["comments"]
            if not comments:
                break
            
            # 获取每条评论的子评论
            if include_sub_comments:
                for comment in comments:
                    if comment["reply_count"] > 0:
                        print(f"  获取评论「{comment['user_name']}」的子评论...")
                        sub_comments = self._get_all_sub_comments(note_id, comment["id"])
                        comment["sub_comments"] = sub_comments
            
            all_comments.extend(comments)
            
            if not result["has_more"]:
                print(f"主评论获取完成，共 {len(all_comments)} 条")
                break
            
            cursor = result.get("cursor", "")
            
            # 不是最后一页时等待
            if page < max_pages:
                self._random_delay()
        
        # 统计总数
        total_main = len(all_comments)
        total_sub = sum(len(c["sub_comments"]) for c in all_comments)
        print(f"\n获取完成！主评论: {total_main} 条，子评论: {total_sub} 条")
        
        return all_comments
    
    def export_comments_to_json(self, comments: List[Dict], filepath: str):
        """导出评论到 JSON 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        print(f"评论已导出到: {filepath}")


def test_scraper():
    """测试函数"""
    print("=" * 60)
    print("小红书评论爬虫 - 优化版测试")
    print("=" * 60)
    
    # 注意：需要先设置 Cookie 才能正常使用
    print("\n使用说明：")
    print("1. 浏览器登录小红书")
    print("2. F12 → Application → Cookies → xiaohongshu.com")
    print("3. 复制 Cookie 字符串")
    print("4. 在代码中设置 scraper.set_cookies('你的Cookie')")
    print("\n示例代码：")
    print("""
from app.scraper_optimized import XiaohongshuScraperOptimized

# 初始化
scraper = XiaohongshuScraperOptimized(
    cookies='你的Cookie字符串',
    use_random_delay=True,
    max_retries=3
)

# 获取所有评论（包含子评论）
comments = scraper.get_all_comments_with_sub(
    note_id='笔记ID',
    max_pages=5,
    include_sub_comments=True
)

# 导出到文件
scraper.export_comments_to_json(comments, 'comments.json')
""")


if __name__ == "__main__":
    test_scraper()
