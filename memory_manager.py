import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class ConversationMemory:
    """Gerencia histórico e contexto das conversas"""
    
    def __init__(self, storage_dir: str = "./conversas"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_session = []
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Adiciona mensagem ao histórico"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.current_session.append(message)
    
    def get_context(self, last_n: int = 5) -> str:
        """Retorna contexto recente"""
        recent = self.current_session[-last_n:]
        context = "HISTÓRICO RECENTE:\n\n"
        for msg in recent:
            context += f"{msg['role'].upper()}: {msg['content']}\n\n"
        return context
    
    def save_session(self, session_id: str):
        """Salva sessão"""
        filepath = self.storage_dir / f"session_{session_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str) -> bool:
        """Carrega sessão"""
        filepath = self.storage_dir / f"session_{session_id}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                self.current_session = json.load(f)
            return True
        return False