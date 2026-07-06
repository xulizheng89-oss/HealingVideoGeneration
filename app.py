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
    script = generate_video_script(topic)
    video_paths = []
    for scene in script.scenes:
        vpath = call_video_generation_api(scene.visual_description, scene.duration)
        video_paths.append(vpath)

    full_narration = " ".join([scene.narration for scene in script.scenes])
    await generate_narration_and_subtitle(full_narration)

    if len(video_paths) == 1:
        return video_paths[0]

    if MOVIEPY_AVAILABLE:
        try:
            clips = [VideoFileClip(p) for p in video_paths]
            final = concatenate_videoclips(clips, method="compose")
            os.makedirs("outputs", exist_ok=True)
            merged_path = os.path.join("outputs", "merged.mp4")
            final.write_videofile(merged_path, codec="libx264", audio_codec="aac")
            final.close()
            for clip in clips:
                clip.close()
            return merged_path
        except Exception:
            pass
    return video_paths[0]

demo = gr.Interface(
    fn=generate_healing_video,
    inputs=gr.Textbox(label="疗愈主题", placeholder="例如：森林冥想、海边呼吸……", lines=2),
    outputs=gr.Video(label="生成的疗愈视频"),
    title="🌿 AI 疗愈视频生成器",
    description="**求职作品 by xulizheng89**  \n输入你想要的疗愈场景，AI 将自动生成视频。",
    examples=[["森林冥想"], ["海边呼吸练习"], ["星空助眠引导"], ["花园晨间散步"]],
    cache_examples=False
)

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    demo.launch(server_name="0.0.0.0")