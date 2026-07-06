import os
import time
import asyncio
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from video_tools import generate_video_script, call_video_generation_api, generate_narration_and_subtitle
from models import VideoScript

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

def merge_videos(video_paths, output_path=None):
    if not MOVIEPY_AVAILABLE or len(video_paths) < 2:
        return video_paths[0] if video_paths else None
    clips = [VideoFileClip(p) for p in video_paths]
    final = concatenate_videoclips(clips, method="compose")
    if output_path is None:
        output_path = os.path.join("outputs", f"merged_{int(time.time())}.mp4")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    final.close()
    for clip in clips:
        clip.close()
    return output_path

async def run_full_pipeline(topic: str):
    # 生成剧本
    script: VideoScript = generate_video_script(topic)
    video_paths = []
    for scene in script.scenes:
        vpath = call_video_generation_api(scene.visual_description, scene.duration)
        video_paths.append(vpath)

    full_narration = " ".join([scene.narration for scene in script.scenes])
    audio_info = await generate_narration_and_subtitle(full_narration)

    merged = merge_videos(video_paths) if len(video_paths) > 1 else video_paths[0]
    main_video = merged or video_paths[0]

    # 只返回视频和简单状态文本
    status_msg = f"生成完成！剧本标题：{script.title}\n音频：{audio_info['audio']}\n字幕：{audio_info['subtitle']}"
    return main_video, status_msg

with gr.Blocks(title="🌿 AI 疗愈视频生成器", css="""
    body { background-color: #f9f7f4; }
    .gradio-container { max-width: 900px; margin: auto; }
    #title { text-align: center; font-size: 2em; color: #5c6b73; margin-top: 20px; }
    .preset-btn { background-color: #e8e2d9; border: none; color: #4a5759; }
    .preset-btn:hover { background-color: #d6ccbc; }
""") as demo:

    gr.HTML("<div id='title'>🌿 AI 疗愈空间 —— 求职作品</div>")
    gr.Markdown("### 👋 中科院硕士 · 专注 AI+心理学。输入主题，即可生成专属疗愈视频。")

    with gr.Row():
        topic_input = gr.Textbox(
            label="视频主题",
            placeholder="例如：雨夜窗边的冥想引导、晨间森林呼吸练习...",
            lines=2,
            scale=4
        )
        submit_btn = gr.Button("生成疗愈视频", variant="primary", scale=1)

    with gr.Row():
        presets = ["森林冥想", "海边呼吸练习", "星空助眠引导", "花园晨间散步"]
        for p in presets:
            btn = gr.Button(p, elem_classes="preset-btn", size="sm")
            btn.click(fn=lambda x=p: x, outputs=topic_input)

    video_output = gr.Video(label="生成的疗愈视频", height=400)
    status_output = gr.Textbox(label="状态", lines=3)

    async def on_submit(topic):
        main_vid, status_msg = await run_full_pipeline(topic)
        return main_vid, status_msg

    submit_btn.click(
        fn=on_submit,
        inputs=topic_input,
        outputs=[video_output, status_output],
        show_progress="full"
    )

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    demo.launch(show_api=False)