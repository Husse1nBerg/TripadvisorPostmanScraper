scheduler = AsyncIOScheduler()
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from app.scrapers.tripadvisor_scraper import scrape_hotel_price

# Initialize the scheduler
scheduler = AsyncIOScheduler()

async def daily_scraping_task():
    # TODO: Replace with actual hotel list from your database
    geo_id = "g155032"
    hotel_id = "d14134983"
    from datetime import date, timedelta
    checkin_date = date.today()
    checkout_date = checkin_date + timedelta(days=1)
    try:
        price = await scrape_hotel_price(
            geo_id=geo_id,
            hotel_id=hotel_id,
            checkin_date=checkin_date,
            checkout_date=checkout_date
        )
        # TODO: Save the price to your database
        print(f"Daily scrape - Price: {price}")
    except Exception as e:
        print(f"Error in daily scraping task: {e}")

# Schedule the task to run every day at midnight
scheduler.add_job(daily_scraping_task, 'cron', hour=0)

def start_scheduler():
    print("Starting scheduler...")
    scheduler.start()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

# If this file is run directly, start the scheduler
if __name__ == "__main__":
    start_scheduler()