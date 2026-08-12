from enum import Enum as PyEnum


class PlatformEnum(str, PyEnum):
    """游戏支持平台枚举。

    独立成模块，供 model 与 schemas 共同引用，避免 model 层反向依赖 schemas 层。
    """
    PC = "电脑端"
    AZ = "安卓端"
    OTHER = "Other"
