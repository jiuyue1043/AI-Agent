"""需求解析 Agent — 将原始需求拆解为结构化用户故事"""

from __future__ import annotations

from typing import Any, Optional

from src.agents.base import BaseAgent
from src.models.schemas import RequirementAnalysis
from src.prompts.templates import PromptTemplates


class RequirementParserAgent(BaseAgent):
    """需求解析 Agent"""

    def __init__(self, llm_client, config: Optional[dict] = None):
        super().__init__(name="requirement_parser", llm_client=llm_client, config=config)

    async def run(self, input_data: Any, context: Optional[dict] = None) -> RequirementAnalysis:
        """
        解析原始需求文本，输出结构化的需求分析结果

        Args:
            input_data: 原始需求文本 (str)
            context: 可选上下文，包含 repo_context

        Returns:
            RequirementAnalysis 对象
        """
        requirement_text = input_data
        repo_context = (context or {}).get("repo_context", "")

        if repo_context:
            repo_context = f"\n以下为现有代码仓库上下文（供参考）:\n{repo_context}"
        else:
            repo_context = ""

        user_prompt = PromptTemplates.REQUIREMENT_PARSER_USER.format(
            requirement_text=requirement_text,
            repo_context=repo_context,
        )

        raw_response = await self._call_llm(
            system_prompt=PromptTemplates.REQUIREMENT_PARSER_SYSTEM,
            user_prompt=user_prompt,
        )

        # 解析 JSON
        data = await self.llm.chat_json(
            system_prompt="将以下内容解析为 JSON 格式，保持原始结构不变。只输出 JSON，不要其他内容。",
            user_prompt=raw_response,
            model=self.config.get("model", "gpt-4o"),
            temperature=0.0,
        )

        return RequirementAnalysis(**data)
