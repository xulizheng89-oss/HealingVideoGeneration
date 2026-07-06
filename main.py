
import os
import time
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

from video_tools import generate_video_script, call_video_generation_api, generate_narration_and_subtitle

app = FastAPI(title="AI 疗愈视频生成器")
templates = Jinja2Templates(directory="templates")

# 输出目录
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, topic: str = Form(...)):
    try:
        # 1. 生成剧本
        script = generate_video_script(topic)

        # 2. 生成视频（逐个场景）
        video_paths = []
        for scene in script.scenes:
            vpath = call_video_generation_api(scene.visual_description, scene.duration)
            video_paths.append(vpath)

        # 3. 生成旁白和字幕（异步）
        full_narration = " ".join([scene.narration for scene in script.scenes])
        audio_info = await generate_narration_and_subtitle(full_narration)

        # 4. 简单合并：如果有多个场景，只取第一个（免费环境合并可能失败，为了稳定，只展示第一个场景视频）
        # 如果你愿意，可以保留 moviepy 合并逻辑，但这里为了稳定简化
        main_video = video_paths[0] if video_paths else None

        if not main_video or not os.path.exists(main_video):
            return HTMLResponse(content="<h2>视频生成失败，请稍后重试。</h2>", status_code=500)

        # 返回包含视频播放的页面
        return templates.TemplateResponse("result.html", {
            "request": request,
            "video_url": f"/outputs/{os.path.basename(main_video)}",
            "topic": topic
        })
    except Exception as e:
        return HTMLResponse(content=f"<h2>生成出错：{str(e)}</h2>", status_code=500)


# 挂载输出目录以提供视频文件
from fastapi.staticfiles import StaticFiles
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")