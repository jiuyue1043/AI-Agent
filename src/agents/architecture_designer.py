"""架构设计 Agent — 根据用户故事设计技术方案"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.agents.base import BaseAgent
from src.models.schemas import RequirementAnalysis, TechDesign
from src.prompts.templates import PromptTemplates


class ArchitectureDesignerAgent(BaseAgent):
    """架构设计 Agent"""

    def __init__(self, llm_client, config: Optional[dict] = None):
        super().__init__(name="architecture_designer", llm_client=llm_client, config=config)

    async def run(self, input_data: Any, context: Optional[dict] = None) -> TechDesign:
        """
        根据需求分析结果设计技术方案

        Args:
            input_data: RequirementAnalysis 对象
            context: 可选上下文，包含 repo_context

        Returns:
            TechDesign 对象
        """
        requirement: RequirementAnalysis = input_data
        repo_context = (context or {}).get("repo_context", "（未提供代码仓库上下文）")

        user_stories_json = json.dumps(
            [story.model_dump() for story in requirement.user_stories],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = PromptTemplates.ARCHITECTURE_USER.format(
            user_stories_json=user_stories_json,
            repo_context=repo_context,
        )

        raw_response = await self._call_llm(
            system_prompt=PromptTemplates.ARCHITECTURE_SYSTEM,
            user_prompt=user_prompt,
        )

        data = await self.llm.chat_json(
            system_prompt="将以下内容解析为 JSON 格式，保持原始结构不变。只输出 JSON，不要其他内容。",
            user_prompt=raw_response,
            model=self.config.get("model", "gpt-4o"),
            temperature=0.0,
        )

        return TechDesign(**data)
