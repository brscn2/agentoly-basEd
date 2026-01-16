import json
import os
from datetime import datetime
from typing import Dict, Any, List
from app.config import settings
from pathlib import Path


class ConversationLogger:
    """Logger for saving tutoring conversations to JSONL file."""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or settings.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "conversations.jsonl"
    
    def log_conversation(
        self,
        conversation_id: str,
        student_id: str,
        topic_id: str,
        messages: List[Dict[str, Any]],
        understanding_level: int = None,
        student_profile: Dict[str, Any] = None,
        topic_info: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """Log a conversation to the JSONL file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": str(conversation_id),
            "student_id": student_id,
            "topic_id": topic_id,
            "understanding_level": understanding_level,
            "student_profile": student_profile or {},
            "topic_info": topic_info or {},
            "messages": messages,
            "message_count": len(messages),
            "metadata": metadata or {}
        }
        
        # Append to JSONL file with pretty formatting
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
    
    def get_conversations(
        self,
        student_id: str = None,
        topic_id: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """Retrieve logged conversations, optionally filtered."""
        if not self.log_file.exists():
            return []
        
        conversations = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if student_id and entry.get("student_id") != student_id:
                        continue
                    if topic_id and entry.get("topic_id") != topic_id:
                        continue
                    conversations.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp (newest first)
        conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        if limit:
            conversations = conversations[:limit]
        
        return conversations


# Global logger instance
logger = ConversationLogger()
