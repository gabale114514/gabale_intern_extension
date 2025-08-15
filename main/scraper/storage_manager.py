from datetime import datetime
from typing import List, Dict
from main.database.database_manager import (
    mark_inactive_topics, 
    save_hot_topic, 
    save_collection_log,
    get_db_manager
)

class StorageManager:
    def __init__(self):
        self.db = get_db_manager()
    
    def save_topics(self, topics: List[Dict], deduplicator) -> Dict[str, int]:
        stats = {'total_count': len(topics), 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        for topic in topics:
            try:
                is_duplicate, existing_id = deduplicator.is_duplicate(topic)
                if is_duplicate and existing_id:
                    update_data = {
                        'rank': topic['rank'],
                        'heat_value': topic['heat_value'],
                        'last_seen_at': datetime.now().isoformat(),
                        'is_active': True
                    }
                    if 'tags' in topic and topic['tags']:
                        update_data['tags'] = topic['tags']
                    if self.db.update_hot_topic(existing_id, update_data):
                        stats['success_count'] += 1
                    stats['duplicate_count'] += 1
                else:
                    topic_data = {**topic,
                        'first_seen_at': datetime.now().isoformat(),
                        'last_seen_at': datetime.now().isoformat(),
                        'tags': topic.get('tags', [])
                    }
                    if save_hot_topic(topic_data):
                        stats['success_count'] += 1
                    else:
                        stats['error_count'] += 1
            except Exception as e:
                stats['error_count'] += 1
        return stats
    
    def mark_inactive_by_category(self, platform_code: str, current_hashes: List[str], category: str):
        mark_inactive_topics(platform_code, current_hashes, category=category)
    
    def save_collection_log(self, platform: str, category: str, status: str, 
                          stats: Dict, start_time: str, end_time: str):
        save_collection_log(
            platform=platform,
            category=category,
            status=status,
            stats=stats,
            start_time=start_time,
            end_time=end_time
        )