import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('shift_scheduler')
    logger.setLevel(logging.INFO)
    
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

logger = setup_logger()
