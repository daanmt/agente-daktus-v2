"""
Structured Logger for Agente Daktus QA
Provides consistent logging across all modules
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class StructuredLogger:
    """Structured logger for Agente Daktus QA with JSON output"""
    
    def __init__(self, name: str = "agent", log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler (only WARNING and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.log_file = log_file
    
    def _create_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Create structured payload for logging"""
        payload = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        return payload
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        payload = self._create_payload(message, **kwargs)
        self.logger.info(json.dumps(payload, ensure_ascii=False))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        payload = self._create_payload(message, **kwargs)
        self.logger.warning(json.dumps(payload, ensure_ascii=False))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        payload = self._create_payload(message, **kwargs)
        self.logger.error(json.dumps(payload, ensure_ascii=False))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        payload = self._create_payload(message, **kwargs)
        self.logger.debug(json.dumps(payload, ensure_ascii=False))
    
    def get_log_path(self) -> str:
        """Get path to log file"""
        return str(self.log_file)


# Global logger instance
logger = StructuredLogger()

