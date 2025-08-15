import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from .utils import clean_text, process_tags, generate_hash, safe_get, parse_json_string

class DataParser:
    @staticmethod
    def parse_api_data(api_data: Dict, platform_code: str, category: str, config: Dict) -> List[Dict]:
        current_data = api_data
        for key in config['data_path']:
            current_data = safe_get(current_data, key)
            if current_data is None:
                return []

        items = parse_json_string(current_data) if config['list_type'] == 'string' else current_data
        if not isinstance(items, list):
            return []

        field_map = config['field_mapping']
        topics = []
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            title = clean_text(safe_get(item, field_map['title'], ""))
            if not title:
                continue
            
            topic = {
                "platform": platform_code,
                "category": category,
                "rank": idx,
                "timestamp": datetime.now().isoformat(),
                "title": title,
                "heat_value": DataParser.extract_heat_value(safe_get(item, field_map['heat'], "")),
                "url": f"https://rebang.today/item/{safe_get(item, field_map['url'], '')}" if safe_get(item, field_map['url'], '') else "",
                "tags": process_tags(clean_text(safe_get(item, field_map['tag'], ""))),
                "hash_id": generate_hash(f"{title}_{platform_code}_{category}")
            }
            topics.append(topic)
        return topics

    @staticmethod
    def extract_heat_value(heat_str: Any) -> Optional[int]:
        if isinstance(heat_str, int):
            return heat_str
        if not heat_str or not isinstance(heat_str, str):
            return None
        match = re.search(r'(\d+\.?\d*)\s*([w万亿]?)', heat_str)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2)
        if unit in ('万', 'w'):
            value *= 10000
        elif unit == '亿':
            value *= 100000000
        return int(value)