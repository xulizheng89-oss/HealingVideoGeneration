
---
title: AI Healing Video Generator
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.31.0
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