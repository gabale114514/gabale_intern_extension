import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from main.database.database_manager import get_db_manager

class Deduplicator:
    def __init__(self):
        self.db = get_db_manager()
        self.config = {
            'hash_id_threshold': 0,
            'title_similarity_threshold': 0.85,
            'time_window_minutes': 30
        }
    
    def is_duplicate(self, topic: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        existing_by_hash = self.db.get_hot_topic_by_hash(topic['hash_id'])
        if existing_by_hash:
            last_seen = existing_by_hash['last_seen_at']
            if last_seen and (datetime.now() - last_seen < timedelta(minutes=self.config['time_window_minutes'])):
                return True, existing_by_hash['id']
        
        time_threshold = datetime.now() - timedelta(minutes=self.config['time_window_minutes'])
        similar_topics = self.db.execute_query("""
            SELECT id, title FROM hot_topics 
            WHERE platform_id = (SELECT id FROM platforms WHERE code = %s)
            AND last_seen_at >= %s
            AND is_active = TRUE
        """, (topic['platform'], time_threshold))
        
        for existing in similar_topics:
            similarity = self._title_similarity(topic['title'], existing['title'])
            if similarity >= self.config['title_similarity_threshold']:
                return True, existing['id']
                
        return False, None
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)