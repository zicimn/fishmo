from pydantic import BaseModel
from typing import List, Optional
from enum import Enum as PyEnum

class GalItem(BaseModel):
    name:str
    cover: str


class GalList(BaseModel):
    total:int
    items:List[GalItem]


class PlatformEnum(str, PyEnum):
    WINDOWS = "Windows"
    MACOS = "macOS"
    LINUX = "Linux"
    EMULATOR = "模拟器"
    ANDROID = "安卓直装"
    OTHER ="Other"