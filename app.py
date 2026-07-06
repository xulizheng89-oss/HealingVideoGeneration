import os
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from video_tools import generate_video_script, call_video_generation_api, generate_narration_and_subtitle

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

async def generate_healing_video(topic: str):
    """输入主题，返回生成的视频路径"""
    # 1. 生成剧本
    script = generate_video_script(topic)

    # 2. 生成所有场景视频
    video_paths = []
    for scene in script.scenes:
        vpath = call_video_generation_api(scene.visual_description, scene.duration)
        video_paths.append(vpath)

    # 3. 生成旁白（这里可以不返回，但让它生成，避免中断）
    full_narration = " ".join([scene.narration for scene in script.scenes])
    await generate_narration_and_subtitle(full_narration)

    # 4. 合并视频（如果只有一个场景，直接返回）
    if len(video_paths) == 1:
        return video_paths[0]

    # 如果有多个场景，尝试合并（需要 moviepy）
    if MOVIEPY_AVAILABLE:
        try:
            clips = [VideoFileClip(p) for p in video_paths]
            final = concatenate_videoclips(clips, method="compose")
            output_dir = "./outputs"
            os.makedirs(output_dir, exist_ok=True)
            merged_path = os.path.join(output_dir, "merged_healing.mp4")
            final.write_videofile(merged_path, codec="libx264", audio_codec="aac")
            final.close()
            for clip in clips:
                clip.close()
            return merged_path
        except Exception:
            return video_paths[0]
    else:
        return video_paths[0]   # 无法合并时返回第一个视频

# 创建简单的 Interface
iface = gr.Interface(
    fn=generate_healing_video,
    inputs=gr.Textbox(
        label="疗愈主题",
        placeholder="例如：森林冥想、海边呼吸练习……",
        lines=2
    ),
    outputs=gr.Video(label="生成的疗愈视频", width=640, height=360),
    title="🌿 AI 疗愈视频生成器",
    description="""
    **求职作品 by xulizheng89**  
    输入你想要的疗愈场景，AI 会自动生成剧本、视频、旁白和字幕。
    """,
    examples=[
        ["森林冥想"],
        ["海边呼吸练习"],
        ["星空助眠引导"],
        ["花园晨间散步"]
    ],
    cache_examples=False,
    allow_flagging="never"
)

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    iface.launch(server_name="0.0.0.0")