import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# JWT 签名密钥：生产环境务必通过环境变量 SECRET_KEY 注入，不要使用代码中的默认值
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
# token 有效期（分钟）
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

