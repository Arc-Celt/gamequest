import os
import logging
from datetime import datetime

def setup_logging(log_name="indexing", logs_dir="logs", with_timestamp=False):
    os.makedirs(logs_dir, exist_ok=True)
    if with_timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logfile = f"{logs_dir}/{log_name}_{timestamp}.log"
    else:
        logfile = f"{logs_dir}/{log_name}.log"
    logging.basicConfig(
        level=logging.INFO,
        filename=logfile,
        filemode='w',
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    return logging.getLogger(log_name)