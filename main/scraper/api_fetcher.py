import random
import time
import logging
import requests
from requests.exceptions import RequestException
from typing import Dict, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ApiFetcher:
    def __init__(self, session: requests.Session, base_url: str):
        self.session = session
        self.base_url = base_url
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        ]
    
    def update_headers(self):
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'{self.base_url}/',
        })
    
    def fetch_data(self, url: str, params: Dict, max_retries: int = 0) -> Optional[Dict]:
        retries = 0
        while retries <= max_retries:
            try:
                self.update_headers()
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except (RequestException, ValueError) as e:
                logger.warning(f"API请求失败 ({retries+1}/{max_retries+1}): {e}")
                retries += 1
                time.sleep(1 * retries)
        return None
