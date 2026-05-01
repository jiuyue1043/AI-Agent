#!/usr/bin/env python3
"""
Requirement Delivery Agent - 入口文件
基于多 Agent 协作的全链路需求交付系统
"""

import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.orchestrator import PipelineOrchestrator

console = Console()


BANNER = r"""
  ____                                    ____       _ _     _
 |  _ \ ___  ___ _   _ _ __ ___   ___   |  _ \  ___| (_) __| | ___
 | |_) / _ \/ __| | | | '_ ` _ \ / _ \  | | | |/ _ \ | |/ _` |/ _ \
 |  _ <  __/\__ \ |_| | | | | | |  __/  | |_| |  __/ | | (_| |  __/
 |_| \_\___||___/\__,_|_| |_| |_|\___|  |____/ \___|_|_|\__,_|\___|

    多 Agent 协作 · 全链路需求交付
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="基于多 Agent 协作的全链路需求交付系统"
    )
    parser.add_argument(
        "--requirement", "-r",
        type=str,
        default="examples/demo_requirement.md",
        help="需求文档路径 (Markdown 格式)"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="目标代码仓库路径 (用于架构设计 Agent 读取上下文)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="outputs",
        help="输出目录"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/settings.yaml",
        help="配置文件路径"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    console.print(BANNER, style="bold cyan")

    # 校验需求文件
    req_path = Path(args.requirement)
    if not req_path.exists():
        console.print(f"[red]错误: 需求文件不存在: {req_path}[/red]")
        sys.exit(1)

    requirement_text = req_path.read_text(encoding="utf-8")

    console.print(Panel(
        f"[bold]需求文件:[/bold] {req_path}\n"
        f"[bold]代码仓库:[/bold] {args.repo or '(未指定，将跳过仓库上下文)'}\n"
        f"[bold]输出目录:[/bold] {args.output}\n"
        f"[bold]配置文件:[/bold] {args.config}",
        title="运行配置",
        border_style="cyan"
    ))

    # 初始化并运行 Pipeline
    orchestrator = PipelineOrchestrator(
        config_path=args.config,
        output_dir=args.output,
        repo_path=args.repo,
    )

    result = await orchestrator.run(requirement_text)

    console.print()
    console.print(Panel(
        "[bold green]Pipeline 执行完成！[/bold green]\n\n"
        f"产出物已保存至: [cyan]{args.output}[/cyan]\n\n"
        f"  - user_stories.json     (结构化用户故事)\n"
        f"  - tech_design.md        (技术方案)\n"
        f"  - generated_code/       (生成代码)\n"
        f"  - generated_tests/      (生成测试)\n"
        f"  - delivery_report.md    (交付报告)",
        title="完成",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
