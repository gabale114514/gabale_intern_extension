import logging
import time
import datetime
class ScraperReporter:
    """采集结果报告器"""
    def __init__(self):
        self.logger = logging.getLogger('scraper.reporter')
        self.total_stats = {
            'platforms': 0,
            'categories': 0,
            'success': 0,
            'duplicate': 0,
            'error': 0,
            'disabled': 0,
            'start_time': time.time()
        }
    
    def log_header(self):
        """记录采集开始信息"""
        self.logger.info("\n" + "="*60)
        self.logger.info(f"热榜今日爬虫 - 开始采集 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*60)
    
    def log_platform_result(self, platform: str, category: str, result: dict):
        """记录单个分类的结果"""
        self.total_stats['categories'] += 1
        
        if 'stats' in result:
            stats = result['stats']
            status = result['status']
            
            self.total_stats['success'] += stats['success_count']
            self.total_stats['duplicate'] += stats['duplicate_count']
            self.total_stats['error'] += stats['error_count']
            
            self.logger.info(
                f"平台 [{platform.upper()}] 分类 [{category}] - {status}\n"
                f"成功: {stats['success_count']} | "
                f"重复: {stats['duplicate_count']} | "
                f"错误: {stats['error_count']}"
            )
        else:
            self.total_stats['error'] += 1
            self.logger.error(
                f"平台 [{platform.upper()}] 分类 [{category}] 采集失败: {result.get('error', '未知错误')}"
            )
    
    def log_summary(self):
        """记录汇总报告"""
        duration = time.time() - self.total_stats['start_time']
        
        summary_msg = f"""
{'='*60}
采集总结报告
{'-'*60}
耗时: {duration:.2f}秒
总平台数: {self.total_stats['platforms']}
总分类数: {self.total_stats['categories']}
成功总数: {self.total_stats['success']}
重复总数: {self.total_stats['duplicate']}
错误总数: {self.total_stats['error']}
禁用平台: {self.total_stats['disabled']}
{'='*60}
        """
        self.logger.info(summary_msg)