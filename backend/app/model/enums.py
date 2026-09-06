from enum import Enum as PyEnum


class PlatformEnum(str, PyEnum):
    PC = "电脑端"
    AZ = "安卓端"
    OTHER = "Other"


class CategoryEnum(str, PyEnum):
    PLOT = "剧情向"
    HEALING = "治愈系"
    DAILY = "日常系"
    ROMANCE = "恋爱模拟"
    ADV = "文字冒险"
    RPG = "RPG"
    MANAGEMENT = "经营模拟"
    ERO = "拔作"
    ALL_AGES = "全年龄"
    OTHER = "其他"


class ReceiveEnum(int, PyEnum):
    article = 0
    galgame = 1
