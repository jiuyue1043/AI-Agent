"""LLM 客户端封装"""

from __future__ import annotations

import json
import logging
from typing import Optional, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMClient:
    """封装 OpenAI API 调用"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o",
    ):
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**kwargs)
        self.default_model = default_model

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[Type[BaseModel]] = None,
    ) -> str:
        """
        调用 LLM 进行对话

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            response_format: Pydantic 模型，用于结构化输出

        Returns:
            LLM 返回的文本内容
        """
        model = model or self.default_model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.beta.chat.completions.parse(**kwargs)
            content = response.choices[0].message.content

            if content is None:
                # 如果使用了 structured output，尝试从 parsed 获取
                parsed = response.choices[0].message.parsed
                if parsed:
                    return parsed.model_dump_json(indent=2)
                raise ValueError("LLM 返回内容为空")

            return content

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """
        调用 LLM 并解析返回的 JSON

        Returns:
            解析后的字典
        """
        raw = await self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 尝试从 markdown code block 中提取 JSON
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # 去掉首尾的 ``` 行
            json_lines = []
            inside = False
            for line in lines:
                if line.strip().startswith("```") and not inside:
                    inside = True
                    continue
                elif line.strip() == "```" and inside:
                    break
                elif inside:
                    json_lines.append(line)
            cleaned = "\n".join(json_lines)

        return json.loads(cleaned)
