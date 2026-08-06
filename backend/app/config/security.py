import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# JWT 签名密钥：生产环境务必通过环境变量 SECRET_KEY 注入，不要使用代码中的默认值
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
# token 有效期（分钟）
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

#resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

# cloundinary
# 注意：API key/secret 的变量名沿用了历史上的拼写错误（CLOUNDDINARY），
# 为了兼容现有 .env 保持不变；新增的 cloud_name 使用正确拼写。
CLOUNDDINARY_API_KEY = os.getenv("CLOUNDDINARY_API_KEY")
CLOUNDDINARY_API_SECRET = os.getenv("CLOUNDDINARY_API_SECRET")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")

