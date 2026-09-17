import logging
from pathlib import Path
from app.config import LOGS_DIR

def setup_logging():
    """تهيئة نظام التسجيل مع ملف منفصل للتصحيح"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    debug_handler = logging.FileHandler(LOGS_DIR / 'app_debug.log')
    debug_handler.setLevel(logging.DEBUG)
    
    main_handler = logging.FileHandler(LOGS_DIR / 'app.log')
    main_handler.setLevel(logging.INFO)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[debug_handler, main_handler, logging.StreamHandler()]
    )