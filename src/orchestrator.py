"""Pipeline 编排器 — 串联所有 Agent"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agents import (
    RequirementParserAgent,
    ArchitectureDesignerAgent,
    CodeGeneratorAgent,
    TestGeneratorAgent,
    ReportGeneratorAgent,
)
from src.models.schemas import (
    RequirementAnalysis,
    TechDesign,
    GeneratedCode,
    GeneratedTest,
    DeliveryReport,
)
from src.utils.llm_client import LLMClient
from src.utils.repo_scanner import RepoScanner

logger = logging.getLogger(__name__)
console = Console()


class PipelineOrchestrator:
    """
    全链路需求交付 Pipeline 编排器

    串联五个 Agent:
    1. 需求解析 → 2. 架构设计 → 3. 代码生成 → 4. 测试生成 → 5. 报告汇总
    """

    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        output_dir: str = "outputs",
        repo_path: Optional[str] = None,
    ):
        self.config = self._load_config(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 LLM 客户端
        llm_config = self.config.get("llm", {})
        self.llm = LLMClient(
            base_url=llm_config.get("base_url"),
            default_model=llm_config.get("model", "gpt-4o"),
        )

        # 扫描仓库上下文
        self.repo_context = ""
        if repo_path:
            scanner = RepoScanner(
                repo_path=repo_path,
                max_depth=self.config.get("repo_scanner", {}).get("max_depth", 4),
                ignore_patterns=self.config.get("repo_scanner", {}).get("ignore_patterns"),
            )
            self.repo_context = scanner.get_full_context()

        # 初始化各 Agent
        agent_configs = self.config.get("agents", {})
        self.requirement_parser = RequirementParserAgent(
            self.llm, agent_configs.get("requirement_parser", {})
        )
        self.architecture_designer = ArchitectureDesignerAgent(
            self.llm, agent_configs.get("architecture_designer", {})
        )
        self.code_generator = CodeGeneratorAgent(
            self.llm, agent_configs.get("code_generator", {})
        )
        self.test_generator = TestGeneratorAgent(
            self.llm, agent_configs.get("test_generator", {})
        )
        self.report_generator = ReportGeneratorAgent(
            self.llm, agent_configs.get("report_generator", {})
        )

    @staticmethod
    def _load_config(path: str) -> dict:
        config_path = Path(path)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        logger.warning(f"配置文件不存在: {path}，使用默认配置")
        return {}

    async def run(self, requirement_text: str) -> DeliveryReport:
        """
        执行完整的 Pipeline

        Args:
            requirement_text: 原始需求文本

        Returns:
            最终的交付报告
        """
        context = {"repo_context": self.repo_context}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # ── Step 1: 需求解析 ──────────────────────────
            task = progress.add_task("[cyan]Step 1/5 需求解析 Agent 运行中...", total=None)
            requirement: RequirementAnalysis = await self.requirement_parser.run(
                requirement_text, context
            )
            self._save_json("user_stories.json", requirement.model_dump())
            progress.update(task, description="[green]Step 1/5 需求解析 ✓")
            progress.stop_task(task)

            console.print(f"  → 生成 {len(requirement.user_stories)} 个用户故事")
            console.print(f"  → 识别 {len(requirement.ambiguities)} 个歧义点")

            # ── Step 2: 架构设计 ──────────────────────────
            task = progress.add_task("[cyan]Step 2/5 架构设计 Agent 运行中...", total=None)
            tech_design: TechDesign = await self.architecture_designer.run(
                requirement, context
            )
            self._save_json("tech_design.json", tech_design.model_dump())
            self._save_text("tech_design.md", self._tech_design_to_md(tech_design))
            progress.update(task, description="[green]Step 2/5 架构设计 ✓")
            progress.stop_task(task)

            console.print(f"  → 涉及 {len(tech_design.affected_modules)} 个模块")
            console.print(f"  → 定义 {len(tech_design.interfaces)} 个接口")

            # ── Step 3: 代码生成 ──────────────────────────
            task = progress.add_task("[cyan]Step 3/5 代码生成 Agent 运行中...", total=None)
            generated_code: GeneratedCode = await self.code_generator.run(
                tech_design, context
            )
            self._save_code_files(generated_code)
            progress.update(task, description="[green]Step 3/5 代码生成 ✓")
            progress.stop_task(task)

            console.print(f"  → 生成 {len(generated_code.files)} 个代码文件")

            # ── Step 4: 测试生成 ──────────────────────────
            task = progress.add_task("[cyan]Step 4/5 测试生成 Agent 运行中...", total=None)
            all_ac = []
            for story in requirement.user_stories:
                all_ac.extend(story.acceptance_criteria)
            generated_test: GeneratedTest = await self.test_generator.run(
                (generated_code, all_ac), context
            )
            self._save_test_files(generated_test)
            progress.update(task, description="[green]Step 4/5 测试生成 ✓")
            progress.stop_task(task)

            console.print(f"  → 生成 {len(generated_test.test_cases)} 个测试用例")

            # ── Step 5: 报告汇总 ──────────────────────────
            task = progress.add_task("[cyan]Step 5/5 报告汇总 Agent 运行中...", total=None)
            report: DeliveryReport = await self.report_generator.run({
                "requirement": requirement,
                "tech_design": tech_design,
                "generated_code": generated_code,
                "generated_test": generated_test,
            })
            self._save_text("delivery_report.md", report.content)
            progress.update(task, description="[green]Step 5/5 报告汇总 ✓")
            progress.stop_task(task)

        return report

    # ── 文件输出辅助方法 ────────────────────────────────

    def _save_json(self, filename: str, data: dict):
        path = self.output_dir / filename
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"已保存: {path}")

    def _save_text(self, filename: str, content: str):
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"已保存: {path}")

    def _save_code_files(self, generated_code: GeneratedCode):
        code_dir = self.output_dir / "generated_code"
        code_dir.mkdir(parents=True, exist_ok=True)

        for file in generated_code.files:
            file_path = code_dir / file.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file.content, encoding="utf-8")
            logger.info(f"已保存代码: {file_path}")

    def _save_test_files(self, generated_test: GeneratedTest):
        test_dir = self.output_dir / "generated_tests"
        test_dir.mkdir(parents=True, exist_ok=True)

        # 按文件分组
        seen_files: dict[str, list] = {}
        for tc in generated_test.test_cases:
            key = tc.name if tc.name.endswith(".py") else f"test_{tc.target_module}.py"
            if key not in seen_files:
                seen_files[key] = []
            seen_files[key].append(tc)

        for filename, cases in seen_files.items():
            # 如果测试用例的 code 都相同（来自同一个文件），只写一次
            unique_codes = list(set(tc.code for tc in cases))
            content = unique_codes[0] if len(unique_codes) == 1 else "\n\n".join(unique_codes)

            file_path = test_dir / filename
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"已保存测试: {file_path}")

    @staticmethod
    def _tech_design_to_md(td: TechDesign) -> str:
        """将技术方案转为 Markdown 格式"""
        lines = [f"# 技术方案\n\n{td.overview}\n"]

        lines.append("## 涉及模块")
        for m in td.affected_modules:
            lines.append(f"- {m}")
        lines.append("")

        if td.interfaces:
            lines.append("## 接口定义")
            for iface in td.interfaces:
                lines.append(f"### `{iface.method} {iface.path}`")
                lines.append(f"{iface.description}")
                if iface.request_body:
                    lines.append(f"\n**请求体:**\n```\n{iface.request_body}\n```")
                if iface.response_body:
                    lines.append(f"\n**响应体:**\n```\n{iface.response_body}\n```")
                lines.append("")

        if td.database_changes:
            lines.append("## 数据库变更")
            for change in td.database_changes:
                lines.append(f"- **{change.operation}** `{change.table}`: {change.description}")
                if change.sql:
                    lines.append(f"  ```sql\n  {change.sql}\n  ```")
            lines.append("")

        if td.design_decisions:
            lines.append("## 技术决策")
            for d in td.design_decisions:
                lines.append(f"- {d}")
            lines.append("")

        if td.risks:
            lines.append("## 技术风险")
            for r in td.risks:
                lines.append(f"- {r}")
            lines.append("")

        return "\n".join(lines)
