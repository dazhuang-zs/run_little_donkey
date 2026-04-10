"""
链接解析模块
支持解析小红书、大众点评、抖音的分享链接
"""
import re
from enum import Enum
from typing import Dict, Optional, Any

class Platform(str, Enum):
    """支持的平台枚举"""
    XIAOHONGSHU = "xiaohongshu"
    DIANPING = "dianping"
    DOUYIN = "douyin"

# 平台正则表达式模式
PLATFORM_PATTERNS = {
    Platform.XIAOHONGSHU: [
        # 小红书分享链接模式
        r"https?://www\.xiaohongshu\.com/explore/([a-f0-9]+)",
        r"https?://www\.xiaohongshu\.com/discovery/item/([a-f0-9]+)",
        r"https?://xhslink\.com/[A-Za-z0-9]+",
    ],
    Platform.DIANPING: [
        # 大众点评分享链接模式
        r"https?://www\.dianping\.com/shop/([A-Za-z0-9]+)",
        r"https?://m\.dianping\.com/shop/([A-Za-z0-9]+)",
        r"https?://www\.dianping\.com/poi/([A-Za-z0-9]+)",
    ],
    Platform.DOUYIN: [
        # 抖音分享链接模式
        r"https?://v\.douyin\.com/[A-Za-z0-9]+",
        r"https?://www\.douyin\.com/video/([0-9]+)",
        r"https?://www\.iesdouyin\.com/share/video/([0-9]+)",
    ]
}

def extract_content_id(url: str, platform: Platform) -> Optional[str]:
    """
    从URL中提取内容ID

    Args:
        url: 分享链接
        platform: 平台类型

    Returns:
        内容ID，如果无法提取则返回None
    """
    patterns = PLATFORM_PATTERNS.get(platform, [])

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            # 如果有捕获组，使用第一个捕获组作为ID
            if match.groups():
                return match.group(1)
            # 否则使用整个匹配的部分（如短链）
            else:
                return match.group(0)

    return None

def parse_xiaohongshu_url(url: str) -> Dict[str, Any]:
    """解析小红书链接"""
    # 小红书短链可能需要重定向获取实际ID，这里简化处理
    content_id = extract_content_id(url, Platform.XIAOHONGSHU)
    if content_id:
        return {
            "success": True,
            "platform": Platform.XIAOHONGSHU,
            "content_id": content_id,
            "url_type": "explore" if "explore" in url else "discovery_item"
        }

    # 如果没有匹配到已知模式，尝试提取可能的ID
    # 小红书ID通常是24位十六进制字符串
    hex_pattern = r"([a-f0-9]{24})"
    match = re.search(hex_pattern, url.lower())
    if match:
        return {
            "success": True,
            "platform": Platform.XIAOHONGSHU,
            "content_id": match.group(1),
            "url_type": "unknown"
        }

    return {
        "success": False,
        "error": "无法解析小红书链接格式"
    }

def parse_dianping_url(url: str) -> Dict[str, Any]:
    """解析大众点评链接"""
    content_id = extract_content_id(url, Platform.DIANPING)
    if content_id:
        return {
            "success": True,
            "platform": Platform.DIANPING,
            "content_id": content_id,
            "url_type": "shop" if "shop" in url else "poi"
        }

    # 尝试提取数字ID
    digit_pattern = r"/(\d+)"
    match = re.search(digit_pattern, url)
    if match:
        return {
            "success": True,
            "platform": Platform.DIANPING,
            "content_id": match.group(1),
            "url_type": "numeric_id"
        }

    return {
        "success": False,
        "error": "无法解析大众点评链接格式"
    }

def parse_douyin_url(url: str) -> Dict[str, Any]:
    """解析抖音链接"""
    content_id = extract_content_id(url, Platform.DOUYIN)
    if content_id:
        return {
            "success": True,
            "platform": Platform.DOUYIN,
            "content_id": content_id,
            "url_type": "video"
        }

    # 尝试提取数字ID
    digit_pattern = r"/(\d{19})"
    match = re.search(digit_pattern, url)
    if match:
        return {
            "success": True,
            "platform": Platform.DOUYIN,
            "content_id": match.group(1),
            "url_type": "video_id"
        }

    return {
        "success": False,
        "error": "无法解析抖音链接格式"
    }

def parse_url(url: str) -> Dict[str, Any]:
    """
    解析分享链接，识别平台并提取内容ID

    Args:
        url: 分享链接

    Returns:
        解析结果字典，包含：
        - success: 是否成功
        - platform: 平台类型（如果成功）
        - content_id: 内容ID（如果成功）
        - url_type: 链接类型
        - error: 错误信息（如果失败）
    """
    if not url or not isinstance(url, str):
        return {
            "success": False,
            "error": "URL不能为空且必须为字符串"
        }

    # 转换为小写以简化匹配
    url_lower = url.lower()

    # 检查平台
    if "xiaohongshu" in url_lower or "xhslink" in url_lower:
        return parse_xiaohongshu_url(url_lower)

    elif "dianping" in url_lower:
        return parse_dianping_url(url_lower)

    elif "douyin" in url_lower or "iesdouyin" in url_lower:
        return parse_douyin_url(url_lower)

    else:
        # 尝试所有平台的通用匹配
        for platform in Platform:
            content_id = extract_content_id(url_lower, platform)
            if content_id:
                return {
                    "success": True,
                    "platform": platform,
                    "content_id": content_id,
                    "url_type": "generic"
                }

    return {
        "success": False,
        "error": "不支持的平台或链接格式。支持：小红书、大众点评、抖音"
    }

# 测试代码
if __name__ == "__main__":
    test_urls = [
        "https://www.xiaohongshu.com/explore/1234567890abcdef12345678",
        "https://xhslink.com/ABC123",
        "https://www.dianping.com/shop/H8f7G9h2",
        "https://v.douyin.com/AbC123XyZ",
        "https://invalid.url.com"
    ]

    for url in test_urls:
        print(f"测试链接: {url}")
        result = parse_url(url)
        print(f"结果: {result}\n")