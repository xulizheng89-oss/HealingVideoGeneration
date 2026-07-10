from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict, Union

# 原有物理状态（保留通用性）
class PhysicsState(BaseModel):
    gravity: bool = Field(description="是否有重力")
    collision_objects: List[str] = Field(default=[], description="碰撞体列表")
    motion: str = Field(description="运动状态描述")
    initial_positions: Optional[Dict[str, Any]] = Field(default=None, description="初始位置")

# 新增：心理物理参数（用于疗愈场景）
class PsychoPhysicalState(BaseModel):
    color_saturation: float = Field(ge=0.0, le=1.0, description="色彩饱和度 (0-1)")
    motion_velocity: float = Field(ge=0.0, le=1.0, description="运动速度系数 (0-1)")
    natural_element_ratio: float = Field(ge=0.0, le=1.0, description="自然元素占比")
    luminance_contrast: float = Field(ge=0.0, le=1.0, description="明暗对比度")
    sound_frequency: Optional[Union[str, int, float]] = Field(None, description="背景声描述（可以是数字或文本）")

# 场景模型（扩展了心理物理状态）
class Scene(BaseModel):
    start: float = Field(description="开始时间（秒）")
    duration: float = Field(description="持续时长（秒）")
    visual_description: str = Field(description="视觉描述")
    narration: str = Field(description="旁白文本")
    physics: PhysicsState = Field(description="物理状态")
    psycho_physical: Optional[PsychoPhysicalState] = Field(None, description="心理物理参数（疗愈用）")

class VideoScript(BaseModel):
    title: str = Field(description="视频标题")
    scenes: List[Scene] = Field(description="分镜列表")