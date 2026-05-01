"""数据模型定义 — 各 Agent 间传递的结构化数据"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AcceptanceCriteria(BaseModel):
    """验收标准"""
    id: str = Field(description="唯一标识，如 AC-01")
    description: str = Field(description="验收标准描述")
    priority: str = Field(default="P0", description="优先级: P0/P1/P2")


class UserStory(BaseModel):
    """用户故事"""
    id: str = Field(description="唯一标识，如 US-01")
    title: str = Field(description="故事标题")
    role: str = Field(description="用户角色")
    action: str = Field(description="用户行为")
    benefit: str = Field(description="期望收益")
    acceptance_criteria: list[AcceptanceCriteria] = Field(default_factory=list)
    priority: str = Field(default="P0", description="优先级")
    estimated_complexity: str = Field(default="medium", description="复杂度: low/medium/high")


class RequirementAnalysis(BaseModel):
    """需求解析 Agent 的输出"""
    project_name: str = Field(description="项目/功能名称")
    summary: str = Field(description="需求概述")
    user_stories: list[UserStory] = Field(description="拆解后的用户故事列表")
    ambiguities: list[str] = Field(default_factory=list, description="识别到的歧义点")
    assumptions: list[str] = Field(default_factory=list, description="假设条件")


class InterfaceDefinition(BaseModel):
    """接口定义"""
    method: str = Field(description="HTTP 方法: GET/POST/PUT/DELETE")
    path: str = Field(description="接口路径")
    description: str = Field(description="接口描述")
    request_body: Optional[str] = Field(default=None, description="请求体描述")
    response_body: Optional[str] = Field(default=None, description="响应体描述")


class DatabaseChange(BaseModel):
    """数据库变更"""
    operation: str = Field(description="操作类型: CREATE_TABLE/ADD_COLUMN/ALTER_COLUMN/CREATE_INDEX")
    table: str = Field(description="表名")
    description: str = Field(description="变更描述")
    sql: Optional[str] = Field(default=None, description="SQL 语句")


class TechDesign(BaseModel):
    """架构设计 Agent 的输出"""
    overview: str = Field(description="技术方案概述")
    affected_modules: list[str] = Field(description="涉及的模块列表")
    interfaces: list[InterfaceDefinition] = Field(default_factory=list, description="接口定义")
    database_changes: list[DatabaseChange] = Field(default_factory=list, description="数据库变更")
    design_decisions: list[str] = Field(default_factory=list, description="关键技术决策")
    risks: list[str] = Field(default_factory=list, description="技术风险")


class CodeFile(BaseModel):
    """生成的代码文件"""
    file_path: str = Field(description="文件路径")
    language: str = Field(description="编程语言")
    content: str = Field(description="文件内容")
    description: str = Field(description="文件说明")


class GeneratedCode(BaseModel):
    """代码生成 Agent 的输出"""
    files: list[CodeFile] = Field(description="生成的文件列表")
    notes: list[str] = Field(default_factory=list, description="补充说明")


class TestCase(BaseModel):
    """测试用例"""
    id: str = Field(description="测试用例 ID")
    name: str = Field(description="测试名称")
    type: str = Field(description="测试类型: unit/integration")
    target_module: str = Field(description="被测模块")
    description: str = Field(description="测试描述")
    code: str = Field(description="测试代码")


class GeneratedTest(BaseModel):
    """测试生成 Agent 的输出"""
    test_cases: list[TestCase] = Field(description="测试用例列表")
    coverage_notes: str = Field(default="", description="覆盖率说明")


class DeliveryReport(BaseModel):
    """报告汇总 Agent 的输出"""
    title: str = Field(description="报告标题")
    content: str = Field(description="报告正文 (Markdown)")
