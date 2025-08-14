import schedule
import time
from datetime import datetime
from main.scraper.rebang_scraper import run_scheduled_scraping, get_db_manager
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
        results = run_scheduled_scraping()
        print("\n采集结果:")
        for platform, res in results.items():
            if 'stats' in res:
                print(f"- {platform}: {res['status']}, 成功保存: {res['stats']['success_count']}, 重复: {res['stats']['total_count'] - res['stats']['success_count'] - res['stats']['error_count']}")
            else:
                print(f"- {platform}: {res['status']}, 错误: {res['error']}")
    except Exception as e:
        print(f"采集过程中发生错误: {e}")
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