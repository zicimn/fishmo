from sqlalchemy import Column, Integer, String, DateTime, Text, SmallInteger
from sqlalchemy.sql import func
from config.db import Base

class User(Base):
    __tablename__ = "user"  # 数据库表名
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # 主键，自增ID
    username = Column(String(50), unique=True, nullable=False, index=True)  # 用户名，唯一，必填，有索引
    email = Column(String(100), unique=True, nullable=False, index=True)  # 邮箱，唯一，必填，有索引 
    password_hash = Column(String(255), nullable=False)  # 密码哈希，必填
    avatar = Column(String(255))  # 头像URL，可选
    bio = Column(Text)  # 个人简介，长文本，可选
    status = Column(SmallInteger, default=1, comment="0-禁用 1-正常")  # 状态，默认正常
    is_admin = Column(SmallInteger, default=0)  # 是否管理员，默认否
    created_at = Column(DateTime, server_default=func.now())  # 创建时间，默认当前时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # 更新时间，自动更新