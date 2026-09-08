from typing import Optional
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ALGORITHM, SECRET_KEY
from fastapi import HTTPException

security = HTTPBearer()  # 自动去掉 header

def verify_login(credentials: Optional[HTTPAuthorizationCredentials]) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供凭证")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload['sub'])  # 从token取出id
        return user_id
    except JWTError:
        raise HTTPException(401, "token无效")


def verify_admin(credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供凭证")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        is_admin = payload.get('is_admin', False)
        if not is_admin:
            raise False #这里不能直接raise
        return True
    except JWTError:
        raise HTTPException(401, "token无效")