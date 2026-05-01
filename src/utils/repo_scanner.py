"""代码仓库扫描工具"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RepoScanner:
    """扫描代码仓库结构，为架构设计 Agent 提供上下文"""

    def __init__(
        self,
        repo_path: str,
        max_depth: int = 4,
        ignore_patterns: Optional[list[str]] = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.max_depth = max_depth
        self.ignore_patterns = ignore_patterns or [
            "node_modules", ".git", "__pycache__", ".venv",
            "venv", "dist", "build", ".next", ".idea", ".vscode",
        ]

    def scan_structure(self) -> str:
        """
        扫描仓库目录结构

        Returns:
            格式化的目录树字符串
        """
        if not self.repo_path.exists():
            return f"(仓库路径不存在: {self.repo_path})"

        lines = [f"{self.repo_path.name}/"]
        self._scan_dir(self.repo_path, lines, prefix="", depth=0)
        return "\n".join(lines)

    def _scan_dir(self, path: Path, lines: list[str], prefix: str, depth: int):
        if depth >= self.max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            return

        # 过滤忽略的目录
        entries = [
            e for e in entries
            if e.name not in self.ignore_patterns and not e.name.startswith(".")
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                self._scan_dir(entry, lines, prefix + child_prefix, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    def scan_key_files(self, max_files: int = 20) -> str:
        """
        扫描关键文件内容（配置文件、入口文件、README 等）

        Returns:
            关键文件内容的汇总字符串
        """
        key_patterns = [
            "README.md", "README.rst",
            "package.json", "pyproject.toml", "setup.py", "setup.cfg",
            "requirements.txt", "Pipfile",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".env.example",
            "Makefile",
            "tsconfig.json",
        ]

        content_parts = []
        count = 0

        for pattern in key_patterns:
            file_path = self.repo_path / pattern
            if file_path.exists() and file_path.is_file():
                try:
                    text = file_path.read_text(encoding="utf-8")
                    # 截断过长的文件
                    if len(text) > 3000:
                        text = text[:3000] + "\n... (截断)"
                    content_parts.append(f"### {pattern}\n```\n{text}\n```")
                    count += 1
                    if count >= max_files:
                        break
                except (UnicodeDecodeError, PermissionError):
                    continue

        if not content_parts:
            return "(未找到关键配置文件)"

        return "\n\n".join(content_parts)

    def get_full_context(self) -> str:
        """获取完整的仓库上下文（目录结构 + 关键文件）"""
        structure = self.scan_structure()
        key_files = self.scan_key_files()

        return f"""## 代码仓库目录结构
            {structure}
            ## 关键配置文件
            {key_files}"""
