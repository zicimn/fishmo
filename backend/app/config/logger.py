import logging
from pathlib import Path

log_dir = Path(__file__).parent.parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# 只配置你自己的应用日志器，不动根日志器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 清除旧处理器
logger.handlers = []
logger.propagate = False  # 不向父级传播

# 文件处理器
file_handler = logging.FileHandler(log_dir / "app.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

logger.info("Logger initialized")