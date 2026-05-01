"""Agent 基类"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self, name: str, llm_client: LLMClient, config: Optional[dict] = None):
        self.name = name
        self.llm = llm_client
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def run(self, input_data: Any, context: Optional[dict] = None) -> Any:
        """执行 Agent 的核心逻辑"""
        ...

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[type] = None,
    ) -> str:
        """调用 LLM 的通用方法"""
        self.logger.info(f"[{self.name}] 调用 LLM ...")
        model = self.config.get("model", "gpt-4o")
        temperature = self.config.get("temperature", 0.3)

        result = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )
        self.logger.info(f"[{self.name}] LLM 调用完成，返回 {len(result)} 字符")
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
