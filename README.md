#AI-Agent
 基于多 Agent 协作的全链路需求交付系统，面向团队日常的产品迭代场景。过去一个中等复杂度的需求从 PRD 评审到代码合并，平均要经历产品、前端、后端、测试四个角色的反复沟通，耗时通常在 3-5 个工作日，其中大量时间浪费在需求理解偏差导致的返工上。这套系统的核心目标就是把这条链路上重复性最高、最容易出错的环节交给 Agent 自动完成。
 整个系统由五个 Agent 串联构成一条完整的推理链。第一个是需求解析 Agent，它接收飞书文档格式的原始需求，自动拆解为结构化的用户故事和验收标准，并标注其中的歧义点供产品经理确认。第二个是架构设计 Agent，它会读取现有代码仓库的目录结构和接口定义，结合需求内容生成技术方案，包括涉及的模块、新增或修改的接口、以及数据库变更。第三个是代码生成 Agent，基于技术方案直接生成可运行的代码骨架和核心业务逻辑，代码风格与仓库现有代码保持一致。第四个是测试 Agent，根据验收标准自动生成单元测试和接口测试用例，并在沙箱环境中运行验证。最后由报告 Agent 汇总整个流程的产出物，生成一份从需求到测试的完整交付报告，推送到团队的审批流程。

##架构概览

原始需求 (飞书/Markdown) 经过以下五个 Agent 依次处理：

①需求解析 Agent → 结构化用户故事 + 验收标准
②架构设计 Agent → 技术方案 + 接口定义 + DB 变更
③代码生成 Agent → 可运行代码骨架 + 核心业务逻辑
④测试生成 Agent → 单元测试 + 集成测试用例
⑤报告汇总 Agent → 完整交付报告 (Markdown)

##快速开始

1. 安装依赖

pip install -r requirements.txt


2. 配置 API Key

export OPENAI_API_KEY="sk-your-key-here"
#或者编辑config/setting.ytml

3. 运行

#使用内置示例需求：python main.py


#使用自定义需求文件：python main.py --requirement examples/demo_requirement.md


#指定目标代码仓库路径：python main.py --requirement examples/demo_requirement.md --repo ./my-project


#指定输出目录：python main.py --requirement examples/demo_requirement.md --output ./my-outputs


4. 查看产出

运行完成后，在 outputs/ 目录下会生成：

 user_stories.json — 结构化用户故事
 tech_design.md — 技术方案文档
 generated_code/ — 生成的代码文件
 generated_tests/ — 生成的测试文件
 delivery_report.md — 完整交付报告

##项目结构

 src/ 下包含：

  agents/ — 五个协作 Agent（base.py, requirement_parser.py, architecture_designer.py, code_generator.py, test_generator.py, report_generator.py）
  models/ — Pydantic 数据模型（schemas.py）
  prompts/ — Prompt 模板（templates.py）
  utils/ — 工具模块（llm_client.py, repo_scanner.py）
  orchestrator.py — 流水线编排器

##配置说明

 编辑 config/settings.yaml 可调整：

 LLM 模型选择（支持 OpenAI 全系列）
 各 Agent 的温度参数
 输出目录
 仓库扫描深度

##技术栈

 Python 3.10+
 OpenAI API（兼容任意 OpenAI 格式 API）
 Pydantic v2
 Rich（终端美化输出）

License
MIT


