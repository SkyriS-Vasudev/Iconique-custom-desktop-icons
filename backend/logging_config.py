import os
import logging
import sys

def setup_logging():
    # Prefer AppData, but fall back to the workspace when that location is not writable.
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    log_candidates = []

    appdata = os.getenv('APPDATA')
    if appdata:
        log_candidates.append(os.path.join(appdata, 'Iconique', 'logs'))

    log_candidates.append(os.path.join(backend_dir, 'logs'))

    log_dir = None
    for candidate in log_candidates:
        try:
            os.makedirs(candidate, exist_ok=True)
            log_dir = candidate
            break
        except OSError:
            continue

    if log_dir is None:
        log_dir = backend_dir

    log_file = os.path.join(log_dir, 'iconique.log')
    
    # Configure logging
    logger = logging.getLogger('iconique')
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to create file logger: {e}", file=sys.stderr)
        
    logger.info(f"Logging initialized. Log file path: {log_file}")
    return logger

# Create a default logger instance
logger = setup_logging()
