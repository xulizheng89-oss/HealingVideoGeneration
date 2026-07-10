<img width="1920" height="869" alt="image" src="https://github.com/user-attachments/assets/f6b23dd1-7546-400a-a996-885049c53617" />


---
title: AI Healing Video Generator
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
python_version: "3.10"
app_file: app.py
pinned: false
---


# AI 疗愈视频生成器

这是一个基于 AIGC 与 Agent 的疗愈内容生成 Demo，集成了 LLM 剧本生成、RAG 知识增强、Stable Diffusion 图像生成和视频合成等功能。

## 如何使用
- 输入你想要的主题（如“森林冥想”），点击生成按钮即可获得一段疗愈视频。
- 你也可以点击预设场景快速体验。

## 技术栈
- Gradio
- LangChain + DeepSeek LLM
- Stable Diffusion + ControlNet
- Hugging Face Spaces 部署

- 📋 本地运行指南（可附在项目README或文档中）
1. 下载代码（克隆仓库）
bash
git clone https://github.com/xulizheng89-oss/HealingVideoGeneration.git
cd HealingVideoGeneration
2. 创建并激活虚拟环境（推荐）
bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate
3. 安装依赖
bash
pip install -r requirements.txt
4. 配置环境变量（新建 .env 文件）
在项目根目录下新建一个名为 .env 的文件，填入以下内容（请替换成你自己的 API Key）：

text
OPENAI_API_KEY=sk-你的腾讯混元API密钥
BASE_URL=https://tokenhub.tencentmaas.com/v1
TEXT_MODEL=deepseek-v4-flash-202605
VIDEO_MODEL=hy-video-1.5
如何获取 API Key？

登录 腾讯云混元大模型控制台

在“API密钥管理”中创建或查看你的 API Key

确保你的账户有足够的额度或余额

5. 运行应用
bash
python app.py
启动后，浏览器访问 http://127.0.0.1:7860 即可体验。

ps：
.env 文件的格式
OPENAI_API_KEY=
BASE_URL=
TEXT_MODEL=deepseek-v4-flash-202605
VIDEO_MODEL=hy-video-1.5（注意选择文生视频模型）
