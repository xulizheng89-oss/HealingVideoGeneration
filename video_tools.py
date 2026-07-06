import os
import time
import json
import requests
import edge_tts  
from gtts import gTTS  # 在文件顶部添加导入
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_classic.tools import tool  
from models import VideoScript, Scene, PhysicsState, PsychoPhysicalState
from rag_retriever import get_retriever

load_dotenv()

# 初始化 LLM
llm = ChatOpenAI(
    model=os.getenv("TEXT_MODEL", "deepseek-v4-flash-202605"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0.7,
    streaming=False,
)

# 获取 RAG 检索器
retriever = get_retriever()

# ---------- 工具 1：生成剧本（含 RAG）----------
def generate_video_script(topic: str) -> VideoScript:
    """
    根据用户主题生成剧本，先检索相关知识库中的疗愈理论或历史案例。
    """
    # 1. RAG 检索
    docs = retriever.invoke(topic)
    context = "\n".join([doc.page_content for doc in docs])
    
    # 2. 构造增强提示（包含心理物理参数要求）
    prompt = f"""
    你是一位环境心理学与数字疗愈专家。请根据以下参考知识和用户主题，生成一个视频剧本。
    
    参考知识：
    {context}
    
    用户主题：{topic}
    
    剧本要求：
    - 包含 3~5 个分镜，总时长约20秒
    - 每个分镜需包含：visual_description（视觉描述）、narration（旁白）、duration（秒）
    - 物理状态（physics）：重力、碰撞体、运动描述、初始位置
    - **新增心理物理参数（psycho_physical）**：color_saturation(0-1), motion_velocity(0-1), natural_element_ratio(0-1), luminance_contrast(0-1), sound_frequency(可选)
    
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
    # 提取 JSON
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(content)
        return VideoScript(**data)
    except Exception as e:
        raise RuntimeError(f"解析失败: {e}, 原始内容: {content}")

# ---------- 工具 2：视频生成 API ----------

def call_video_generation_api(visual_description: str, duration: float) -> str:
    """
    调用腾讯云混元视频生成模型，返回本地保存的视频路径。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("BASE_URL")
    submit_url = f"{base_url}/api/video/submit"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": os.getenv("VIDEO_MODEL", "hy-video-1.5"), "prompt": visual_description, "duration": duration}
    
    try:
        resp = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        task_id = resp.json().get("id")
        if not task_id:
            raise Exception("提交任务失败，未获得任务ID")
        
        query_url = f"{base_url}/api/video/query"
        max_attempts = 60
        for attempt in range(max_attempts):
            query_resp = requests.post(query_url, json={"id": task_id, "model": os.getenv("VIDEO_MODEL")}, headers=headers, timeout=30)
            data = query_resp.json()
            status = data.get("status")
            if status in ("DONE", "completed"):
                video_url = data.get("data", {}).get("url") or data.get("ResultVideoUrl")
                if not video_url:
                    raise Exception("视频URL为空")
                output_dir = "./outputs"
                os.makedirs(output_dir, exist_ok=True)
                video_data = requests.get(video_url, timeout=60).content
                filepath = os.path.join(output_dir, f"video_{task_id}_{int(time.time())}.mp4")
                with open(filepath, "wb") as f:
                    f.write(video_data)
                return filepath
            elif status in ("FAIL", "ERROR", "failed"):
                error_msg = data.get("message", "未知错误")
                raise Exception(f"生成失败: {error_msg}")
            time.sleep(5)
        raise Exception("生成超时")
    except Exception as e:
        raise RuntimeError(f"视频生成API错误: {str(e)}")

# ---------- 工具 3：生成旁白和字幕 ----------



async def generate_narration_and_subtitle(text: str) -> Dict[str, str]:
    import os
    import time
    from gtts import gTTS  # 如果顶部已导入，这里不需要重复

    output_dir = "./outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    audio_path = os.path.join(output_dir, f"narration_{timestamp}.mp3")
    subtitle_path = os.path.join(output_dir, f"subtitle_{timestamp}.srt")

    # 使用 gTTS 生成音频
    try:
        tts = gTTS(text, lang="zh-cn", slow=False)
        tts.save(audio_path)
    except Exception as e:
        print(f"TTS 生成失败: {e}")
        # 创建一个空的占位文件，避免后续报错
        with open(audio_path, "w") as f:
            f.write("TTS failed")
        audio_path = None

    # 生成字幕（同步）
    sentences = [s.strip() for s in text.replace('，', ',').replace('。', '.').split('.') if s.strip()]
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

    return {"audio": audio_path, "subtitle": subtitle_path}

def format_time(sec):
    h = int(sec//3600)
    m = int((sec%3600)//60)
    s = int(sec%60)
    ms = int((sec%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

from langchain_core.tools import tool as langchain_tool

# 将普通函数包装成 LangChain 工具（用于 Agent）
tools_for_agent = [
    langchain_tool(generate_video_script, description="根据主题生成视频剧本"),
    langchain_tool(call_video_generation_api, description="根据视觉描述生成视频片段"),
    langchain_tool(generate_narration_and_subtitle, description="生成旁白音频和字幕"),
]