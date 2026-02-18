import os
import logging
from datetime import datetime
import structlog

class CustomLogger:
    _configured = False  # Class variable to track if structlog is configured
    
    def __init__(self, log_dir="logs"):
        self.log_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.log_dir, log_file)
    
    def get_logger(self, name=__file__):
        logger_name = os.path.basename(name)
        
        # Configure structlog only once
        if not CustomLogger._configured:
            # Configure stdlib logging first
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Set up root logger
            logging.basicConfig(
                level=logging.INFO,
                format="%(message)s",
                handlers=[console_handler, file_handler],
                force=True  # Force reconfiguration
            )
            
            # Configure structlog to use stdlib logging backend
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.EventRenamer(to="event"),
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                ],
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
            # Set up formatter for stdlib handlers
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            CustomLogger._configured = True

        return structlog.get_logger(logger_name)