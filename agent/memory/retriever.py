from typing import List, Dict, Any
from agent.memory.storage import BaseStorage

class Retriever:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        all_data = self.storage.get_all()
        # Simple keyword matching for demonstration
        results = []
        for item in all_data:
            content = str(item.get('content', '')).lower()
            if query.lower() in content:
                results.append(item)
        
        return results[:limit]
