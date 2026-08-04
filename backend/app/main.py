from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import user_router, email_router
import uvicorn
from config.security import SECRET_KEY, RESEND_API_KEY


app = FastAPI()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(email_router)

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True,reload_excludes=["logs/*", "*.log", "__pycache__/*"])