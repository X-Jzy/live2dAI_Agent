# Live2D AI Agent

一种基于Live2D + TTS + ASR + LLM + RAG + Qdrant 的AI陪伴模型

## 项目简介

Live2D AI Agent 是一个智能AI助手项目，结合了Live2D动画、语音识别（ASR）、语音合成（TTS）、大语言模型（LLM）、检索增强生成（RAG）和向量数据库（Qdrant），为用户提供沉浸式的AI陪伴体验。

## 功能特性

- **语音交互**：支持实时语音识别和语音合成，实现自然对话
- **Live2D动画**：集成Live2D角色动画，根据对话内容展示表情和动作
- **智能记忆**：使用RAG和Qdrant实现长期记忆和知识检索
- **邮件监听**：自动监听邮件并通知用户
- **游戏监听**：检测用户正在运行的游戏并进行相关对话
- **时间监听**：在特定时间或节日主动发起对话
- **图像分析**：支持图片上传和分析功能
- **天气查询**：集成天气API，提供实时天气信息
- **多语言支持**：支持中文、日文、英文等语言

## 技术栈

- **前端界面**：PySide6 (Qt)
- **语音识别**：FunASR
- **语音合成**：GPT-SoVITS 或其他TTS服务
- **大语言模型**：Ollama + Qwen模型
- **向量数据库**：Qdrant
- **图数据库**：Neo4j (用于知识图谱)
- **Live2D集成**：WebSocket通信

## 安装要求

- Python 3.8+
- Ollama (用于运行本地LLM)
- Qdrant (向量数据库)
- Neo4j (图数据库，可选)
- Live2D应用 (如Hiyori)

## 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/live2d-ai-agent.git
   cd live2d-ai-agent/gui
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装和配置Ollama**
   - 下载并安装Ollama: https://ollama.ai/
   - 拉取Qwen模型：
     ```bash
     ollama pull qwen3.5:2b
     ```

4. **启动Qdrant**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

5. **配置Live2D应用**
   - 确保Live2D应用运行在指定端口 (默认: ws://127.0.0.1:10086)

## 配置

项目使用YAML配置文件 `config.yaml` 进行配置。主要配置项包括：

- **LLM设置**：API密钥、模型选择、温度等
- **TTS设置**：服务地址、语音参数等
- **ASR设置**：模型选择等
- **Live2D设置**：WebSocket地址等
- **邮件监听**：IMAP服务器配置
- **游戏监听**：进程名称映射

## 使用方法

1. **启动应用**
   ```bash
   python main.py
   ```

2. **界面操作**
   - 使用文本输入框发送消息
   - 点击语音按钮进行语音交互
   - 上传图片进行分析

3. **实时对话**
   - 启动实时对话模式，系统会监听语音输入

## 项目结构

```
gui/
├── main.py              # 主程序入口
├── config.py            # 配置加载器
├── config.yaml          # 配置文件
├── llm.py               # LLM接口
├── tts.py               # 语音合成
├── asr.py               # 语音识别
├── live2d_api.py        # Live2D通信
├── audio_record.py      # 音频录制
├── vad.py               # 语音活动检测
├── email_listening.py   # 邮件监听
├── game_listening.py    # 游戏监听
├── time_listening.py    # 时间监听
├── memory/              # 记忆系统
│   ├── rag.py           # RAG检索
│   └── graph_memory.py  # 图记忆
├── tools/               # 工具模块
├── pic_cap/             # 图片捕获
├── weather/             # 天气查询
└── ui/                  # UI资源
```

## 开发与贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

1. 安装开发依赖
2. 配置本地数据库
3. 运行测试

### 代码规范

- 使用Black进行代码格式化
- 遵循PEP 8风格指南
- 添加适当的文档字符串

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- [FunASR](https://github.com/alibaba-damo-academy/FunASR) - 语音识别
- [Ollama](https://ollama.ai/) - 本地LLM运行
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [PySide6](https://wiki.qt.io/Qt_for_Python) - GUI框架
- [Live2D](https://www.live2d.com/) - 动画技术

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。
