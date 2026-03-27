# Live2D AI Agent

一种基于Live2D + TTS + ASR + LLM + RAG + Qdrant 的AI陪伴模型

## 项目简介

Live2D AI Agent 是一个智能AI助手项目，结合了Live2D动画、语音识别（ASR）、语音合成（TTS）、大语言模型（LLM）、检索增强生成（RAG）和向量数据库（Qdrant），为用户提供沉浸式的AI陪伴体验。

目前仍处于开发早期阶段，并且没有太强的写GUI的意愿，(〃＞目＜)

## 功能特性

- **语音交互**：支持实时语音识别和语音合成，实现自然对话
- **智能记忆**：使用RAG和Qdrant实现长期记忆和知识检索
- **Live2D动画**：集成Live2DEX的API操作角色动画，根据对话内容展示表情和动作
- **智能记忆**：使用RAG和Qdrant实现长期记忆和知识检索，Neo4j的知识图谱做记忆与知识辅助
- **邮件监听**：自动监听邮件并通知用户
- **游戏监听**：检测用户正在运行的游戏并进行相关对话
- **时间监听**：在特定时间或节日主动发起对话
- **图像分析**：支持图片上传和分析功能
- **天气查询**：集成天气API，提供实时天气信息
- **多语言支持**：支持中文、日文、英文等语言
- **屏幕获取**：支持获取用户屏幕上的信息
- **天气查询**：集成天气API，提供实时天气信息
- **联网搜索**：使用duckduckgo进行联网搜索
- **屏幕轮询**：打开屏幕轮询模式可轮询获取用户屏幕内容并进行互动

知识图谱：

![img1](https://github.com/X-Jzy/live2dAI_Agent/blob/main/imgs/1.png)

游戏陪玩： 目前针对具体游戏的对话质量一般，未来会接入知识库

![img2](https://github.com/X-Jzy/live2dAI_Agent/blob/main/imgs/2.png)

![img3](https://github.com/X-Jzy/live2dAI_Agent/blob/main/imgs/3.png)

## 技术栈

- **前端界面**：PySide6 (Qt)
- **语音识别**：FunASR
- **语音合成**：GPT-SoVITS 或其他TTS服务
- **大语言模型**：Ollama + Qwen模型
- **向量数据库**：Qdrant
- **图数据库**：Neo4j (用于知识图谱)
- **Live2D集成**：WebSocket通信

## 更新日志

|日期| 功能|
|-----------|-----------|
|3.20| Neo4j知识图谱，知识存储及其对应检索Tools|
|3.27| 屏幕轮询功能，流式tts处理与播放|
