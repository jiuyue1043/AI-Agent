"""Pipeline 集成测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.schemas import (
    RequirementAnalysis,
    UserStory,
    AcceptanceCriteria,
    TechDesign,
    GeneratedCode,
    CodeFile,
    GeneratedTest,
    TestCase,
    DeliveryReport,
)


@pytest.fixture
def sample_requirement():
    return RequirementAnalysis(
        project_name="用户积分系统",
        summary="构建积分激励体系提升用户活跃度",
        user_stories=[
            UserStory(
                id="US-01",
                title="积分获取",
                role="注册用户",
                action="完成平台行为获取积分",
                benefit="获得积分奖励提升参与感",
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id="AC-01",
                        description="发布内容后积分增加10分",
                        priority="P0",
                    )
                ],
                priority="P0",
                estimated_complexity="medium",
            )
        ],
        ambiguities=["积分过期策略未明确"],
        assumptions=["积分永久有效"],
    )


@pytest.fixture
def sample_tech_design():
    return TechDesign(
        overview="基于事件驱动的积分系统设计",
        affected_modules=["user", "points", "content"],
        interfaces=[],
        database_changes=[],
        design_decisions=["采用事件溯源模式记录积分变更"],
        risks=["高并发下积分一致性保障"],
    )


@pytest.fixture
def sample_generated_code():
    return GeneratedCode(
        files=[
            CodeFile(
                file_path="models/point.py",
                language="python",
                content="class Point:\n    pass",
                description="积分数据模型",
            )
        ],
        notes=[],
    )


@pytest.fixture
def sample_generated_test():
    return GeneratedTest(
        test_cases=[
            TestCase(
                id="TC-01",
                name="test_point_creation",
                type="unit",
                target_module="models.point",
                description="测试积分创建",
                code="def test_point_creation():\n    assert True",
            )
        ],
        coverage_notes="1 个测试用例",
    )


class TestModels:
    """数据模型测试"""

    def test_user_story_creation(self, sample_requirement):
        story = sample_requirement.user_stories[0]
        assert story.id == "US-01"
        assert story.priority == "P0"
        assert len(story.acceptance_criteria) == 1

    def test_requirement_analysis_serialization(self, sample_requirement):
        data = sample_requirement.model_dump()
        assert "project_name" in data
        assert "user_stories" in data
        assert isinstance(data["user_stories"], list)

    def test_tech_design_model(self, sample_tech_design):
        assert len(sample_tech_design.affected_modules) == 3
        assert "事件溯源" in sample_tech_design.design_decisions[0]

    def test_generated_code_model(self, sample_generated_code):
        assert len(sample_generated_code.files) == 1
        assert sample_generated_code.files[0].language == "python"


class TestOrchestrator:
    """编排器测试（使用 mock）"""

    def test_output_directory_creation(self, tmp_path):
        from src.orchestrator import PipelineOrchestrator

        output_dir = tmp_path / "test_outputs"
        # 不实际调用 LLM，只验证初始化
        with patch("src.orchestrator.LLMClient"):
            orch = PipelineOrchestrator.__new__(PipelineOrchestrator)
            orch.output_dir = output_dir
            orch.output_dir.mkdir(parents=True, exist_ok=True)
            assert output_dir.exists()
