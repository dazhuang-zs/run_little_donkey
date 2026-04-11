"""
LLM 评论分析模块
支持 OpenAI、Claude 等大模型
"""
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    summary: List[str]
    pitfalls: List[str]
    uncertain: List[str]
    raw_response: str = ""


class CommentAnalyzer:
    """评论分析器"""
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的小红书评论分析助手。请从用户提供的评论数据中，提取有价值的信息。

评论数据包括主评论和子评论（用户之间的互相回复），请综合分析。

请按以下三类输出：

1. 【有用总结】：
   - 提取真实用户体验
   - 产品/服务的优缺点
   - 使用感受和效果
   - 性价比分析
   - 优先提取点赞数高的评论

2. 【避坑指南】：
   - 识别负面评价
   - 质量问题
   - 服务问题
   - 虚假宣传
   - 需要注意的警告信息

3. 【待确认】：
   - 信息不明确的内容
   - 需要进一步验证的问题
   - 用户之间有争议的观点

输出格式要求：
- 返回纯 JSON，不要其他文字
- JSON 结构如下：
{
    "summary": ["总结1", "总结2", "..."],
    "pitfalls": ["避坑1", "避坑2", "..."],
    "uncertain": ["疑问1", "疑问2", "..."]
}

注意事项：
- 每类 3-8 条即可，不需要太多
- 每条简洁明了，不要太长
- 优先选点赞数高的评论
- 子评论中的补充信息也要考虑
- 保持客观，不要添加主观推测
"""
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: str = None,
        model: str = None,
        base_url: str = None
    ):
        """
        初始化分析器
        
        Args:
            provider: 模型提供商 (openai, claude, qwen, mock)
            api_key: API Key
            model: 模型名称
            base_url: API 基础 URL
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "")
        
        # 默认模型
        if model is None:
            if self.provider == "openai":
                self.model = "gpt-3.5-turbo"
            elif self.provider == "claude":
                self.model = "claude-3-haiku-20240307"
            elif self.provider == "qwen":
                self.model = "qwen-turbo"
            else:
                self.model = "gpt-3.5-turbo"
        else:
            self.model = model
        
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        if self.provider == "mock":
            return
        
        try:
            if self.provider == "openai" or self.provider == "qwen":
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url if self.base_url else None
                )
            elif self.provider == "claude":
                try:
                    import anthropic
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                except ImportError:
                    print("未安装 anthropic 库，使用 mock 模式")
                    self.provider = "mock"
        except Exception as e:
            print(f"初始化 LLM 客户端失败: {e}")
            print("将使用 mock 模式")
            self.provider = "mock"
    
    def _format_comments(self, comments: List[Dict]) -> str:
        """将评论列表格式化为文本"""
        lines = []
        
        for idx, comment in enumerate(comments, 1):
            # 主评论
            main_content = comment.get("content", "")
            user_name = comment.get("user_name", "匿名用户")
            liked = comment.get("liked_count", 0)
            
            lines.append(f"【评论 {idx}】@{user_name} (点赞:{liked})")
            lines.append(f"  {main_content}")
            
            # 子评论
            sub_comments = comment.get("sub_comments", [])
            for sub_idx, sub in enumerate(sub_comments, 1):
                sub_user = sub.get("user_name", "匿名")
                sub_content = sub.get("content", "")
                target_user = sub.get("target_user_name", "")
                sub_liked = sub.get("liked_count", 0)
                
                if target_user:
                    lines.append(f"  回复 {idx}.{sub_idx} @{sub_user} → @{target_user} (点赞:{sub_liked})")
                else:
                    lines.append(f"  回复 {idx}.{sub_idx} @{sub_user} (点赞:{sub_liked})")
                lines.append(f"    {sub_content}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _filter_and_sort_comments(
        self,
        comments: List[Dict],
        max_comments: int = 80
    ) -> List[Dict]:
        """
        过滤和排序评论
        
        策略：
        1. 按点赞数排序
        2. 优先选点赞数高的
        3. 包含有子评论的
        """
        # 复制一份
        comments_copy = comments.copy()
        
        # 计算权重
        def comment_weight(c):
            weight = c.get("liked_count", 0) * 10
            weight += len(c.get("sub_comments", [])) * 5
            return weight
        
        # 排序
        comments_copy.sort(key=comment_weight, reverse=True)
        
        # 限制数量
        return comments_copy[:max_comments]
    
    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 调用失败: {e}")
            raise
    
    def _call_claude(self, prompt: str) -> str:
        """调用 Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Claude API 调用失败: {e}")
            raise
    
    def _call_mock(self, prompt: str) -> str:
        """模拟返回（用于测试）"""
        mock_result = {
            "summary": [
                "产品性价比高，适合学生党入手",
                "包装精美，物流速度快",
                "使用效果不错，肤感舒适"
            ],
            "pitfalls": [
                "部分用户反馈实物与图片有色差",
                "客服响应较慢，售后处理不及时",
                "量有点少，不适合多人分享"
            ],
            "uncertain": [
                "是否正品？建议先买小包装试试",
                "质保期多长时间？需要确认",
                "适合什么肤质？因人而异"
            ]
        }
        return json.dumps(mock_result, ensure_ascii=False)
    
    def analyze(self, comments: List[Dict]) -> AnalysisResult:
        """
        分析评论
        
        Args:
            comments: 评论列表
            
        Returns:
            AnalysisResult 对象
        """
        # 过滤和排序评论
        filtered_comments = self._filter_and_sort_comments(comments)
        
        # 格式化评论
        comments_text = self._format_comments(filtered_comments)
        
        # 构建提示词
        prompt = f"请分析以下小红书评论：\n\n{comments_text}"
        
        # 调用 LLM
        try:
            if self.provider == "openai" or self.provider == "qwen":
                response = self._call_openai(prompt)
            elif self.provider == "claude":
                response = self._call_claude(prompt)
            else:
                response = self._call_mock(prompt)
        except Exception as e:
            print(f"LLM 调用失败，使用 mock 模式: {e}")
            response = self._call_mock(prompt)
        
        # 解析结果
        try:
            # 尝试提取 JSON
            json_str = self._extract_json(response)
            result_dict = json.loads(json_str)
            
            return AnalysisResult(
                summary=result_dict.get("summary", []),
                pitfalls=result_dict.get("pitfalls", []),
                uncertain=result_dict.get("uncertain", []),
                raw_response=response
            )
        except Exception as e:
            print(f"解析 LLM 响应失败: {e}")
            return AnalysisResult(
                summary=["解析失败，请查看原始响应"],
                pitfalls=[],
                uncertain=[],
                raw_response=response
            )
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()
        
        # 查找第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        
        if start != -1 and end != -1 and start < end:
            return text[start:end+1]
        
        return text


def test_analyzer():
    """测试分析器"""
    print("=" * 60)
    print("评论分析器测试")
    print("=" * 60)
    
    # 模拟评论数据
    mock_comments = [
        {
            "id": "1",
            "content": "这个产品真的很好用！性价比很高，推荐大家购买！",
            "user_name": "小红薯",
            "liked_count": 128,
            "reply_count": 5,
            "sub_comments": [
                {
                    "id": "1-1",
                    "content": "真的吗？我也想买",
                    "user_name": "小明",
                    "target_user_name": "小红薯",
                    "liked_count": 10
                },
                {
                    "id": "1-2",
                    "content": "我用了觉得一般般",
                    "user_name": "小华",
                    "target_user_name": "小红薯",
                    "liked_count": 3
                }
            ]
        },
        {
            "id": "2",
            "content": "包装很精美，物流也很快，两天就到了",
            "user_name": "美妆达人",
            "liked_count": 56,
            "reply_count": 0,
            "sub_comments": []
        },
        {
            "id": "3",
            "content": "大家注意！实物和图片有色差，慎买！",
            "user_name": "避坑小能手",
            "liked_count": 89,
            "reply_count": 12,
            "sub_comments": [
                {
                    "id": "3-1",
                    "content": "我也发现了！色差挺明显的",
                    "user_name": "买家1号",
                    "target_user_name": "避坑小能手",
                    "liked_count": 25
                }
            ]
        }
    ]
    
    # 使用 mock 模式测试
    analyzer = CommentAnalyzer(provider="mock")
    result = analyzer.analyze(mock_comments)
    
    print("\n【有用总结】")
    for item in result.summary:
        print(f"✅ {item}")
    
    print("\n【避坑指南】")
    for item in result.pitfalls:
        print(f"⚠️ {item}")
    
    print("\n【待确认】")
    for item in result.uncertain:
        print(f"❓ {item}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_analyzer()
