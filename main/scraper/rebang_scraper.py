import logging
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from main.scraper.api_fetcher import ApiFetcher
from main.scraper.data_parser import DataParser
from main.scraper.deduplicator import Deduplicator
from main.scraper.storage_manager import StorageManager
from config.database_config import DATABASE_CONFIG
from main.database.database_manager import get_db_manager              
from config.platform_config import PLATFORM_CONFIG, platform_categories, custom_params
from main.scraper.utils import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

class RebangScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://rebang.today"
        self.api_fetcher = ApiFetcher(self.session, self.base_url)
        self.data_parser = DataParser()
        self.deduplicator = Deduplicator()
        self.storage_manager = StorageManager()
        self.platform_config = PLATFORM_CONFIG
    
    def scrape_platform_category(self, platform_code: str, category: str, extra_params: Optional[Dict] = None):
        """爬取单个平台的单个分类"""
        config = self.platform_config.get(platform_code)
        if not config:
            logger.error(f"平台 {platform_code} 无配置，跳过")
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        
        # 合并参数
        params = config['default_params'].copy()
        params['sub_tab'] = category
        if extra_params:
            params.update(extra_params)
        params['t'] = int(time.time() * 1000)
        
        # 获取数据
        api_data = self.api_fetcher.fetch_data(config['base_url'], params)
        if not api_data:
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        
        # 解析数据
        topics = self.data_parser.parse_api_data(api_data, platform_code, category, config)
        if not topics:
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        
        # 存储数据
        current_hashes = [t['hash_id'] for t in topics]
        self.storage_manager.mark_inactive_by_category(platform_code, current_hashes, category)
        save_stats = self.storage_manager.save_topics(topics, self.deduplicator)
        
        return topics, save_stats
    
    def scrape_platform(self, platform_code: str, categories: List[str], extra_params: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        爬取单个平台的多个分类
        :param platform_code: 平台代码
        :param categories: 分类列表
        :param extra_params: 额外参数
        :return: 各分类的爬取结果
        """
        category_results = {}
        for category in categories:
            try:
                start_time = datetime.now()
                topics, stats = self.scrape_platform_category(platform_code, category, extra_params)
                end_time = datetime.now()

                status = 'success' if stats['success_count'] == stats['total_count'] else \
                        'partial' if stats['success_count'] > 0 else 'failed'

                # 保存日志
                self.storage_manager.save_collection_log(
                    platform=platform_code,
                    category=category,
                    status=status,
                    stats=stats,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )

                category_results[category] = {
                    'status': status,
                    'stats': stats,
                    'duration': (end_time - start_time).total_seconds()
                }
                logger.info(f"平台 {platform_code} 分类 {category} 完成: 成功 {stats['success_count']} 条")
            except Exception as e:
                logger.error(f"平台 {platform_code} 分类 {category} 异常: {e}")
                category_results[category] = {'status': 'error', 'error': str(e)}
        return category_results
    
    def scrape_all_platforms(self, platform_categories: Dict[str, List[str]], platform_extra_params: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
        """
        爬取所有平台的多个分类
        :param platform_categories: 平台-分类映射
        :param platform_extra_params: 各平台的额外参数
        :return: 各平台的爬取结果
        """
        results = {}
        platform_extra_params = platform_extra_params or {}
        
        enabled_platforms = self.deduplicator.db.get_enabled_platforms()
        enabled_codes = {p['code'] for p in enabled_platforms}
        
        for platform_code, categories in platform_categories.items():
            if platform_code not in enabled_codes:
                logger.info(f"平台 {platform_code} 已禁用，跳过所有分类")
                continue
                
            try:
                extra_params = platform_extra_params.get(platform_code, {})
                platform_result = self.scrape_platform(platform_code, categories, extra_params)
                results[platform_code] = platform_result
            except Exception as e:
                logger.error(f"平台 {platform_code} 整体异常: {e}")
                results[platform_code] = {'status': 'error', 'error': str(e)}
                
        return results

_scraper_instance = None

def get_scraper() -> RebangScraper:
    global _scraper_instance
    if not _scraper_instance:
        _scraper_instance = RebangScraper()
    return _scraper_instance

def run_scheduled_scraping(platform_categories: Dict[str, List[str]], 
                        platform_extra_params: Optional[Dict[str, Dict]] = None):
    logger.info("开始定时采集所有平台")
    scraper = get_scraper()
    # 传入platform_categories参数
    results = scraper.scrape_all_platforms(
        platform_categories=platform_categories,
        platform_extra_params=platform_extra_params
    )
    total_success = 0
    for platform_results in results.values():
        if isinstance(platform_results, dict):
            for category_result in platform_results.values():
                if 'stats' in category_result:
                    total_success += category_result['stats']['success_count']
    logger.info(f"定时采集完成，总成功数: {total_success}")
    return results

if __name__ == "__main__":
    print(f"热榜今日爬虫 - 开始采集 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    db = get_db_manager()
    if not db.connect():
        print("数据库连接失败")
        exit(1)
    try:
        rebangscraper=RebangScraper()
        # 3. 执行爬取，传入两个参数
        results = rebangscraper.scrape_all_platforms(
            platform_categories=platform_categories,
            platform_extra_params=custom_params
        )
        
        # 4. 打印结果
        print("\n采集结果:")
        for platform, category_results in results.items():
            print(f"\n平台 {platform}:")
            for category, res in category_results.items():
                if 'stats' in res:
                    print(f"  分类 {category}: {res['status']}, "
                          f"成功保存: {res['stats']['success_count']}, "
                          f"重复: {res['stats']['duplicate_count']}, "
                          f"错误: {res['stats']['error_count']}")
                else:
                    print(f"  分类 {category}: {res['status']}, 错误: {res['error']}")
    finally:
        db.disconnect()