import logging
from typing import Dict, List
from datetime import datetime

class InMemoryLogHandler(logging.Handler):
    """Captures logs in memory for a specific run_id"""
    
    def __init__(self, run_id: str, storage: Dict[str, List[str]]):
        super().__init__()
        self.run_id = run_id
        self.storage = storage
        if run_id not in storage:
            storage[run_id] = []
    
    def emit(self, record):
        try:
            msg = self.format(record)
            # Extract the actual message from JSON if present
            if '"event"' in msg:
                import json
                try:
                    data = json.loads(msg)
                    event = data.get('event', msg)
                    level = data.get('level', 'info').upper()
                    msg = f"[{level}] {event}"
                except:
                    pass
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {msg}"
            self.storage[self.run_id].append(log_entry)
        except Exception:
            self.handleError(record)
