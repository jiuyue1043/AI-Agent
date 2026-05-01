"""测试生成 Agent — 根据代码和验收标准生成测试用例"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from src.agents.base import BaseAgent
from src.models.schemas import GeneratedCode, GeneratedTest, TestCase
from src.prompts.templates import PromptTemplates


class TestGeneratorAgent(BaseAgent):
    """测试生成 Agent"""

    def __init__(self, llm_client, config: Optional[dict] = None):
        super().__init__(name="test_generator", llm_client=llm_client, config=config)

    async def run(self, input_data: Any, context: Optional[dict] = None) -> GeneratedTest:
        """
        根据生成的代码和验收标准生成测试用例

        Args:
            input_data: tuple[GeneratedCode, list[AcceptanceCriteria]]
            context: 可选上下文

        Returns:
            GeneratedTest 对象
        """
        generated_code, acceptance_criteria = input_data

        # 整理代码文本
        code_text = "\n\n".join(
            f"### {f.file_path}\n```{f.language}\n{f.content}\n```"
            for f in generated_code.files
        )

        ac_json = json.dumps(
            [ac.model_dump() for ac in acceptance_criteria],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = PromptTemplates.TEST_GENERATOR_USER.format(
            generated_code_text=code_text,
            acceptance_criteria_json=ac_json,
        )

        raw_response = await self._call_llm(
            system_prompt=PromptTemplates.TEST_GENERATOR_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        # 解析测试文件
        test_cases = self._parse_test_cases(raw_response)

        return GeneratedTest(
            test_cases=test_cases,
            coverage_notes=f"共生成 {len(test_cases)} 个测试用例",
        )

    @staticmethod
    def _parse_test_cases(response: str) -> list[TestCase]:
        """从响应中解析测试用例"""
        pattern = r"===FILE:\s*(.+?)===\s*\n(.*?)===END_FILE==="
        matches = re.findall(pattern, response, re.DOTALL)

        test_cases = []
        for i, (file_path, content) in enumerate(matches):
            file_path = file_path.strip()
            content = content.strip()

            # 尝试提取测试函数名
            func_names = re.findall(r"def\s+(test_\w+)", content)
            target_module = file_path.replace("test_", "").replace("tests/", "")

            for j, func_name in enumerate(func_names):
                test_cases.append(TestCase(
                    id=f"TC-{i + 1}-{j + 1}",
                    name=func_name,
                    type="unit" if "unit" in file_path.lower() or "test_" in file_path else "integration",
                    target_module=target_module,
                    description=f"测试用例: {func_name}",
                    code=content,
                ))

            if not func_names:
                test_cases.append(TestCase(
                    id=f"TC-{i + 1}",
                    name=file_path,
                    type="unit",
                    target_module=target_module,
                    description=f"测试文件: {file_path}",
                    code=content,
                ))

        return test_cases
