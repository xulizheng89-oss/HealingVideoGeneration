import os
import subprocess
import gradio as gr
from dotenv import load_dotenv
import shutil
import subprocess

import imageio_ffmpeg
import subprocess

load_dotenv()

from video_tools import generate_video_script, call_video_generation_api, generate_narration_and_subtitle, merge_audio_video

async def generate_healing_video(topic: str):
    # 1. 生成剧本
    script = generate_video_script(topic)

    # 2. 生成所有场景视频
    video_paths = []
    for scene in script.scenes:
        vpath = call_video_generation_api(scene.visual_description, scene.duration)
        video_paths.append(vpath)

    # 3. 生成旁白音频和字幕
    full_narration = " ".join([scene.narration for scene in script.scenes])
    audio_info = await generate_narration_and_subtitle(full_narration)
    audio_path = audio_info["audio"]  # 例如 ./outputs/narration_xxxxx.mp3

    # 4. 合成视频（取第一个场景或合并多个场景）
    if len(video_paths) == 1:
        raw_video = video_paths[0]
    else:
        # 如果有多个场景，可以用 moviepy 合并，或简单取第一个
        raw_video = video_paths[0]

    # 5. 将音频合入视频（如果音频存在）
    if audio_path and os.path.exists(audio_path):
        output_dir = "./outputs"
        os.makedirs(output_dir, exist_ok=True)
        final_video_path = os.path.join(output_dir, "final_healing_video.mp4")

        try:
            # 使用 imageio_ffmpeg 自带的 ffmpeg（无需系统安装）
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

            cmd = [
                ffmpeg_path,
                "-i", raw_video,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y",
                final_video_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return final_video_path

        except Exception as e:
            print(f"音频合成失败: {e}")
            return raw_video
    else:
        return raw_video


demo = gr.Interface(
    fn=generate_healing_video,
    inputs=gr.Textbox(label="疗愈主题", placeholder="例如：森林冥想、海边呼吸……", lines=2),
    outputs=gr.Video(label="生成的疗愈视频"),
    title="🌿 AI 疗愈视频生成器",
    description="**求职作品 by xulizheng89**  \n输入你想要的疗愈场景，AI 将自动生成带有旁白音频的疗愈视频。",
    examples=[["森林冥想"], ["海边呼吸练习"], ["星空助眠引导"], ["花园晨间散步"]],
    cache_examples=False
)

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    demo.launch(server_name="0.0.0.0", server_port=7860)