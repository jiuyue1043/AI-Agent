"""报告汇总 Agent — 生成完整交付报告"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.agents.base import BaseAgent
from src.models.schemas import (
    RequirementAnalysis,
    TechDesign,
    GeneratedCode,
    GeneratedTest,
    DeliveryReport,
)
from src.prompts.templates import PromptTemplates


class ReportGeneratorAgent(BaseAgent):
    """报告汇总 Agent"""

    def __init__(self, llm_client, config: Optional[dict] = None):
        super().__init__(name="report_generator", llm_client=llm_client, config=config)

    async def run(self, input_data: Any, context: Optional[dict] = None) -> DeliveryReport:
        """
        汇总所有产出物，生成交付报告

        Args:
            input_data: dict 包含所有前置 Agent 的输出

        Returns:
            DeliveryReport 对象
        """
        requirement: RequirementAnalysis = input_data["requirement"]
        tech_design: TechDesign = input_data["tech_design"]
        generated_code: GeneratedCode = input_data["generated_code"]
        generated_test: GeneratedTest = input_data["generated_test"]

        # 构建代码摘要
        code_summary_lines = []
        for f in generated_code.files:
            code_summary_lines.append(
                f"- `{f.file_path}` ({f.language}): {f.description}"
            )
        code_summary = "\n".join(code_summary_lines) if code_summary_lines else "(无)"

        # 构建测试摘要
        test_summary_lines = []
        for tc in generated_test.test_cases:
            test_summary_lines.append(f"- [{tc.id}] {tc.name} ({tc.type})")
        test_summary = "\n".join(test_summary_lines) if test_summary_lines else "(无)"

        user_prompt = PromptTemplates.REPORT_GENERATOR_USER.format(
            requirement_analysis_json=json.dumps(
                requirement.model_dump(), ensure_ascii=False, indent=2
            ),
            tech_design_json=json.dumps(
                tech_design.model_dump(), ensure_ascii=False, indent=2
            ),
            generated_code_summary=code_summary,
            generated_test_summary=test_summary,
        )

        report_content = await self._call_llm(
            system_prompt=PromptTemplates.REPORT_GENERATOR_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        return DeliveryReport(
            title=f"交付报告: {requirement.project_name}",
            content=report_content,
        )
