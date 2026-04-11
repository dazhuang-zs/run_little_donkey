#!/usr/bin/env python3
"""
小红书笔记爬虫 - Markdown 导出工具
用法: python3 export_markdown.py <笔记链接> <cookie>
"""
import sys
import json
import re
import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from apis.xhs_pc_apis import XHS_Apis


def generate_markdown(note_data: dict, comments: list) -> str:
    """生成 Markdown 格式的笔记导出内容"""
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
    
    # ========== 评论数据 ==========
    lines.append("## 💬 评论数据")
    lines.append("")
    
    if not comments:
        lines.append("（暂无评论）")
    else:
        # 按点赞数排序
        sorted_comments = sorted(comments, key=lambda x: int(x.get('liked_count', 0) or 0), reverse=True)
        
        lines.append(f"**📊 共 {len(comments)} 条一级评论**（按点赞数从高到低排列）")
        lines.append("")
        
        for idx, comment in enumerate(sorted_comments, 1):
            likes_count = int(comment.get('liked_count', 0) or 0)
            sub_comments = comment.get('sub_comments', []) or []
            
            # 高赞标记
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
                for sub_idx, sub in enumerate(sub_comments[:5], 1):
                    sub_likes = int(sub.get('liked_count', 0) or 0)
                    sub_hot = "🔥" if sub_likes >= 5 else ""
                    content = sub.get('content', '')[:100]
                    lines.append(f"> - {sub.get('user_nickname', '用户')} ({sub_likes}赞): {content}")
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


def parse_comment(raw_comments: list) -> list:
    """解析评论数据"""
    comments = []
    for comment in raw_comments:
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


def parse_note_info(note_info: dict) -> dict:
    """解析笔记信息"""
    data = note_info.get('data', {})
    items = data.get('items', [])
    
    if not items:
        return {}
    
    note = items[0]
    note_card = note.get('note_card', {})
    interact_info = note_card.get('interact_info', {})
    user_info = note_card.get('user', {})
    
    return {
        'note_id': note.get('id', ''),
        'title': note_card.get('display_title', '') or note_card.get('title', ''),
        'desc': note_card.get('desc', ''),
        'type': note_card.get('type', 'normal'),
        'user_nickname': user_info.get('nick_name', '') or user_info.get('nickname', ''),
        'user_id': user_info.get('user_id', '') or user_info.get('userId', ''),
        'liked_count': interact_info.get('liked_count', '0'),
        'collected_count': interact_info.get('collected_count', '0'),
        'comment_count': interact_info.get('comment_count', '0'),
        'create_time': note_card.get('time', ''),
    }


def export_note(note_url: str, cookie: str) -> str:
    """导出笔记和评论为 Markdown"""
    xhs_apis = XHS_Apis()
    
    # 获取笔记详情
    success, msg, note_info = xhs_apis.get_note_info(note_url, cookie)
    if not success:
        return f"❌ 获取笔记失败: {msg}"
    
    note_data = parse_note_info(note_info)
    note_data['url'] = note_url
    
    # 获取评论
    success, msg, comments = xhs_apis.get_note_all_comment(note_url, cookie)
    if not success:
        return f"❌ 获取评论失败: {msg}"
    
    parsed_comments = parse_comment(comments)
    
    # 生成 Markdown
    markdown = generate_markdown(note_data, parsed_comments)
    
    return markdown


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 export_markdown.py <笔记链接> <cookie>")
        print("示例: python3 export_markdown.py 'https://www.xiaohongshu.com/explore/xxx' 'a1=xxx;web_session=xxx'")
        sys.exit(1)
    
    note_url = sys.argv[1]
    cookie = sys.argv[2]
    
    print("🔍 正在获取笔记数据...", file=sys.stderr)
    result = export_note(note_url, cookie)
    
    if result.startswith("❌"):
        print(result)
        sys.exit(1)
    else:
        print(result)
