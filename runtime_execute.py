import schedule
import time
from datetime import datetime
from main.database.database_manager import get_db_manager
from main.scraper import rebang_scraper
from config.platform_config import platform_categories, custom_params

def scheduled_job():
    """定时任务执行的函数"""
    print(f"\n{'='*50}")
    print(f"开始定时采集任务 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"{'='*50}")
    
    db = get_db_manager()
    if not db.connect():
        print("数据库连接失败")
        return
    
    try:
        # 执行爬取任务
        results = rebang_scraper.run_scheduled_scraping(
            platform_categories=platform_categories,
            platform_extra_params=custom_params
        )
        
        print("\n采集结果详情:")
        total_success = 0
        total_duplicate = 0
        total_error = 0
        
        # 处理每个平台的结果
        for platform, platform_results in results.items():
            print(f"\n平台 {platform}:")
            
            # 处理每个分类的结果
            for category, res in platform_results.items():
                if isinstance(res, dict):
                    # 获取统计信息，使用get方法避免KeyError
                    success = res.get('stats', {}).get('success_count', 0)
                    duplicate = res.get('stats', {}).get('duplicate_count', 0)
                    error = res.get('stats', {}).get('error_count', 0)
                    status = res.get('status', 'unknown')
                    
                    total_success += success
                    total_duplicate += duplicate
                    total_error += error
                    
                    print(f"  - 分类 {category}: {status}, "
                        f"成功: {success}, "
                        f"重复: {duplicate}, "
                        f"错误: {error}")
                else:
                    print(f"  - 分类 {category}: 结果格式异常")
        
        # 打印总结报告
        print(f"\n{'='*30}")
        print(f"总结报告:")
        print(f"总成功数: {total_success}")
        print(f"总重复数: {total_duplicate}")
        print(f"总错误数: {total_error}")
        print(f"{'='*30}")
        
    except Exception as e:
        print(f"采集过程中发生错误: {str(e)}")
    finally:
        db.disconnect()
        print(f"\n{'='*50}")
        print(f"任务完成 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"{'='*50}\n")

if __name__ == "__main__":
    # 设置定时任务
    schedule.every(2).minutes.do(scheduled_job)
    # 立即执行一次
    scheduled_job()
    # 保持程序运行
    print("定时采集服务已启动，等待执行...")
    while True:
        schedule.run_pending()
        time.sleep(1)
        