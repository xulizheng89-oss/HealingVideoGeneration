import os
import time
import json
import requests
import re
import asyncio
import edge_tts
from typing import Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool as langchain_tool
from models import VideoScript
from rag_retriever import get_retriever
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

load_dotenv()

# 初始化 LLM
llm = ChatOpenAI(
    model=os.getenv("TEXT_MODEL", "deepseek-v4-flash-202605"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0.7,
    streaming=False,
)

retriever = get_retriever()

# ---------- 工具 1：生成剧本（含 RAG）----------
def generate_video_script(topic: str) -> VideoScript:
    docs = retriever.invoke(topic)
    context = "\n".join([doc.page_content for doc in docs])
    prompt = f"""
    你是一位环境心理学与数字疗愈专家。请根据以下参考知识和用户主题，生成一个视频剧本。
    
    参考知识：
    {context}
    
    用户主题：{topic}
    
    剧本要求：
    - 包含 1 个分镜，总时长约5秒
    - 每个分镜需包含：visual_description（视觉描述）、narration（旁白）、duration（秒）
    - 物理状态（physics）：重力、碰撞体、运动描述、初始位置
    - 心理物理参数（psycho_physical）：color_saturation(0-1), motion_velocity(0-1), natural_element_ratio(0-1), luminance_contrast(0-1), sound_frequency(可选)
    
    请以 JSON 格式输出，严格遵循以下结构：
    {{
        "title": "视频标题",
        "scenes": [
            {{
                "start": 0.0,
                "duration": 5.0,
                "visual_description": "...",
                "narration": "...",
                "physics": {{ "gravity": true, "collision_objects": [], "motion": "...", "initial_positions": {{}} }},
                "psycho_physical": {{ "color_saturation": 0.7, "motion_velocity": 0.3, "natural_element_ratio": 0.8, "luminance_contrast": 0.4 }}
            }}
        ]
    }}
    仅输出 JSON，不要其他内容。
    """
    response = llm.invoke(prompt)
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(content)
        script = VideoScript(**data)
        # 工业级检查：确保剧本中至少有一个场景
        if not script.scenes:
            raise RuntimeError("生成的剧本中没有场景，请重试或更换主题")
        return script
    except Exception as e:
        raise RuntimeError(f"解析失败: {e}, 原始内容: {content}")

        

# ---------- 工具 2：视频生成 API ----------
@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(RuntimeError),
    before_sleep=lambda retry_state: print(f"视频生成失败，正在重试第 {retry_state.attempt_number} 次..."),
)

def call_video_generation_api(visual_description: str, duration: float) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("BASE_URL")
    submit_url = f"{base_url}/api/video/submit"          # 必须存在
    query_url = f"{base_url}/api/video/query"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("VIDEO_MODEL", "hy-video-1.5"),
        "prompt": visual_description,
        "duration": duration
    }
    try:
        print(f"[VIDEO] 准备提交任务，模型：{os.getenv('VIDEO_MODEL')}，描述长度：{len(visual_description)}字")
        resp = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        print(f"[VIDEO] 提交请求完成，HTTP状态码：{resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        print(f"[VIDEO] 提交响应体：{data}")

        task_id = data.get("id")
        if not task_id:
            print("[VIDEO] 错误：响应中没有 id 字段")
            raise RuntimeError(f"未获取到任务ID，完整响应：{data}")

        print(f"[VIDEO] 任务已提交，ID：{task_id}，开始轮询...")
        
        start = time.time()
        max_total = 300

        for i in range(60):
            elapsed = time.time() - start
            print(f"[VIDEO] 轮询第 {i+1}/60 次，已耗时 {elapsed:.0f} 秒")
            if elapsed > max_total:
                print(f"[VIDEO] 错误：总超时 {max_total} 秒")
                raise RuntimeError(f"任务 {task_id} 总超时")

            qr = requests.post(query_url, json={"id": task_id, "model": os.getenv("VIDEO_MODEL")}, headers=headers, timeout=30)
            qd = qr.json()
            status = qd.get("status")
            print(f"[VIDEO] 任务状态：{status}")

            if status in ("DONE", "completed"):
                print("[VIDEO] 视频生成成功，正在下载...")
                video_url = qd.get("data", {}).get("url") or qd.get("ResultVideoUrl")
                if not video_url:
                    print("[VIDEO] 错误：成功但无视频URL")
                    raise RuntimeError("成功但无视频URL")
                os.makedirs("./outputs", exist_ok=True)
                vdata = requests.get(video_url, timeout=120).content
                filepath = f"./outputs/video_{task_id}_{int(time.time())}.mp4"
                with open(filepath, "wb") as f:
                    f.write(vdata)
                print(f"[VIDEO] 视频已保存到 {filepath}")
                return filepath

            elif status in ("FAIL", "ERROR", "failed"):
                msg = qd.get("message", "未知错误")
                print(f"[VIDEO] 任务失败：{msg}")
                raise RuntimeError(f"任务失败：{msg}")

            time.sleep(5)

        print("[VIDEO] 轮询结束，任务未完成")
        raise RuntimeError("轮询次数耗尽")

    except Exception as e:
        print(f"[VIDEO] 发生异常：{e}")
        raise RuntimeError(f"视频生成API错误: {str(e)}")

# ---------- 工具 3：生成旁白和字幕 ----------
async def generate_narration_and_subtitle(text: str) -> Dict[str, str]:
    print(f"[TTS] 开始生成旁白，文本长度：{len(text)}字")
    output_dir = "./outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    audio_path = os.path.join(output_dir, f"narration_{timestamp}.mp3")
    subtitle_path = os.path.join(output_dir, f"subtitle_{timestamp}.srt")

    audio_success = False
    for attempt in range(3):
        try:
            print(f"[TTS] 第 {attempt+1}/3 次尝试...")
            
            communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
            await communicate.save(audio_path)
            print(f"[TTS] 音频保存成功：{audio_path}")
            audio_success = True
            break
        except Exception as e:
            print(f"[TTS] 失败：{e}")
            if attempt < 2:
                await asyncio.sleep(5)

    # 字幕生成
    try:
        print("[TTS] 开始生成字幕...")
        sentences = [s.strip() for s in re.split(r'[，,。.！!？?]', text) if s.strip()]
        if not sentences:
            sentences = [text]
        total_duration = len(text) * 0.2
        per_dur = total_duration / len(sentences)
        subs = []
        cur = 0.0
        for i, sent in enumerate(sentences):
            start = cur
            end = cur + per_dur
            subs.append(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{sent}\n")
            cur = end
        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write("\n".join(subs))
        print(f"[TTS] 字幕生成成功：{subtitle_path}")
    except Exception as e:
        print(f"[TTS] 字幕生成失败：{e}")

    return {
        "audio": audio_path if audio_success else None,
        "subtitle": subtitle_path if os.path.exists(subtitle_path) else None
    }

def format_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# 工具列表（供 Agent 使用）
tools_for_agent = [
    langchain_tool(generate_video_script, description="根据主题生成视频剧本"),
    langchain_tool(call_video_generation_api, description="根据视觉描述生成视频片段"),
    langchain_tool(generate_narration_and_subtitle, description="生成旁白音频和字幕"),
]