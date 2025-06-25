[English Version](README.md) | [中文版](README_CN.md)

# 旅行助手

本项目是一个旅行助手，帮助用户规划行程，提供目的地信息、活动建议和旅行小贴士。它实现了一个多模态、可反馈、自动化的智能旅行规划助手，充分利用了大语言模型、流程编排、外部API集成和多轮人机交互等现代AI技术。

## 环境配置

- 在项目根目录下创建 `.env` 文件。
- 在 `.env` 文件中添加以下环境变量：
  - `OPENAI_API_KEY`
  - `OPENWEATHER_KEY`
  - `TAVILY_API_KEY`
  - `LANGCHAIN_API_KEY`
  - `LANGCHAIN_TRACING_V2`

## 技术栈

- **LangGraph**：用于构建和管理多节点、多状态的流程图，实现旅行规划的多步推理与反馈循环。
- **LangChain**：集成大语言模型（如 OpenAI GPT-4o），用于自然语言理解、信息抽取和生成。
- **OpenAI GPT-4o**：核心大模型，负责理解用户输入、抽取地点、生成子话题、总结搜索结果和生成旅行计划。
- **Requests**：用于访问外部API（天气、地理位置、网页搜索）。
- **python-dotenv**：用于加载和管理环境变量（API密钥等）。
- **FFmpeg + Whisper**：用于从视频中提取音频并转录为文本，实现多模态输入。
- **缓存与状态管理**：如 `lru_cache`、内存型 checkpointer，保证流程可中断、可恢复。

## 流程概览

### 环境配置
- 加载API密钥，初始化大模型和流程图。

### 用户输入处理
- 支持文本和视频输入。
- 对于视频，使用FFmpeg提取音频，并用Whisper转录为文本。
