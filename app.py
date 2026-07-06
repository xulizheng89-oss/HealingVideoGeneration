
import os
import time
import asyncio
import gradio as gr
from dotenv import load_dotenv

# 加载环境变量（本地可用 .env，Hugging Face 用 Secrets）
load_dotenv()

# 导入你已有的工具函数
from video_tools import generate_video_script, call_video_generation_api, generate_narration_and_subtitle
from models import VideoScript

# 可选：合并视频用
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


def merge_videos(video_paths, output_path=None):
    """合并多个视频为单个文件（需要 moviepy）"""
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
    """
    完整生成流程：剧本 → 视频 → 旁白/字幕。
    返回：(主视频路径, 剧本JSON字符串, 音频路径, 字幕路径, 所有视频列表)
    """
    # 1. 生成剧本
    script: VideoScript = generate_video_script(topic)

    # 2. 为每个场景生成视频
    video_paths = []
    for scene in script.scenes:
        vpath = call_video_generation_api(scene.visual_description, scene.duration)
        video_paths.append(vpath)

    # 3. 拼接所有旁白，生成音频和字幕
    full_narration = " ".join([scene.narration for scene in script.scenes])
    audio_info = await generate_narration_and_subtitle(full_narration)

    # 4. 合并视频（如果安装了 moviepy）
    merged = merge_videos(video_paths) if len(video_paths) > 1 else video_paths[0]
    main_video = merged or video_paths[0]

    # 5. 整理输出信息
    script_json = script.model_dump_json(indent=2, ensure_ascii=False)
    all_videos_text = "\n".join([f"- {p}" for p in video_paths])

    return main_video, script_json, audio_info["audio"], audio_info["subtitle"], all_videos_text


# ========== Gradio 界面 ==========
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

    # 预设示例
    with gr.Row():
        presets = ["森林冥想", "海边呼吸练习", "星空助眠引导", "花园晨间散步"]
        for p in presets:
            btn = gr.Button(p, elem_classes="preset-btn", size="sm")
            btn.click(fn=lambda x=p: x, outputs=topic_input)

    # 输出组件
    video_output = gr.Video(label="生成的疗愈视频", height=400)
    script_output = gr.JSON(label="剧本详情")
    audio_output = gr.Audio(label="旁白音频", type="filepath")
    subtitle_output = gr.File(label="字幕文件 (.srt)")
    all_videos_output = gr.Textbox(label="所有生成视频文件路径", visible=False)  # 隐藏，但保留信息

    # 绑定事件
    async def on_submit(topic):
        main_vid, script_json, audio, sub, all_vids = await run_full_pipeline(topic)
        return main_vid, script_json, audio, sub, all_vids

    submit_btn.click(
        fn=on_submit,
        inputs=topic_input,
        outputs=[video_output, script_output, audio_output, subtitle_output, all_videos_output],
        show_progress="full"
    )


if __name__ == "__main__":
    # 创建输出目录
    os.makedirs("outputs", exist_ok=True)
    demo.launch()