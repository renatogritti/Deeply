import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name):
    """
    Configura um logger com as seguintes características:
    - Logs em arquivo com rotação (max 5MB, max 5 backups)
    - Logs no console
    - Formato: [TIMESTAMP] LEVEL MODULE - MESSAGE
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Cria diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Handler para arquivo
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato do log
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
