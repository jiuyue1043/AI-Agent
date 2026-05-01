"""代码生成 Agent — 根据技术方案生成代码"""

from __future__ import annotations

import re
from typing import Any, Optional

from src.agents.base import BaseAgent
from src.models.schemas import TechDesign, GeneratedCode, CodeFile
from src.prompts.templates import PromptTemplates


class CodeGeneratorAgent(BaseAgent):
    """代码生成 Agent"""

    def __init__(self, llm_client, config: Optional[dict] = None):
        super().__init__(name="code_generator", llm_client=llm_client, config=config)

    async def run(self, input_data: Any, context: Optional[dict] = None) -> GeneratedCode:
        """
        根据技术方案生成代码文件

        Args:
            input_data: TechDesign 对象
            context: 可选上下文，包含 repo_context

        Returns:
            GeneratedCode 对象
        """
        tech_design: TechDesign = input_data
        repo_context = (context or {}).get("repo_context", "（未提供代码仓库上下文）")

        import json
        tech_design_json = json.dumps(
            tech_design.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = PromptTemplates.CODE_GENERATOR_USER.format(
            tech_design_json=tech_design_json,
            repo_context=repo_context,
        )

        raw_response = await self._call_llm(
            system_prompt=PromptTemplates.CODE_GENERATOR_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        # 解析文件
        files = self._parse_files(raw_response)

        return GeneratedCode(files=files, notes=[])

    @staticmethod
    def _parse_files(response: str) -> list[CodeFile]:
        """从 LLM 响应中解析代码文件"""
        pattern = r"===FILE:\s*(.+?)===\s*\n(.*?)===END_FILE==="
        matches = re.findall(pattern, response, re.DOTALL)

        files = []
        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()

            # 推断语言
            ext = file_path.rsplit(".", 1)[-1] if "." in file_path else "unknown"
            lang_map = {
                "py": "python", "js": "javascript", "ts": "typescript",
                "jsx": "javascript", "tsx": "typescript",
                "java": "java", "go": "go", "rs": "rust",
                "sql": "sql", "yaml": "yaml", "yml": "yaml",
                "json": "json", "md": "markdown", "html": "html", "css": "css",
            }
            language = lang_map.get(ext, ext)

            files.append(CodeFile(
                file_path=file_path,
                language=language,
                content=content,
                description=f"自动生成的 {language} 文件",
            ))

        # 如果没有匹配到标准格式，尝试按代码块解析
        if not files:
            code_blocks = re.findall(r"```(\w*)\n(.*?)```", response, re.DOTALL)
            for i, (lang, code) in enumerate(code_blocks):
                if lang.lower() in ("bash", "shell", "sh", "text", ""):
                    continue
                files.append(CodeFile(
                    file_path=f"generated_{i + 1}.{lang or 'txt'}",
                    language=lang or "unknown",
                    content=code.strip(),
                    description=f"生成的代码文件 #{i + 1}",
                ))

        return files
