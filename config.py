import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    TEXT_MODEL = os.getenv("TEXT_MODEL", "deepseek-v4-flash-202605")
    VIDEO_MODEL = os.getenv("VIDEO_MODEL", "hy-video-1.5")
    OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
    