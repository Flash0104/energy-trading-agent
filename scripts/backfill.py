import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from app.services.smard import SmardClient
from app.services.weather import WeatherClient
from src.db.database import SessionLocal, engine
from src.db.models import Base, DayAheadPrice, WeatherData

async def backfill_weather(days=30):
    print(f"Fetching last {days} days of Weather data...")
    client = WeatherClient()
    db = SessionLocal()
    
    # OpenMeteo 'forecast' endpoint is for future, 'archive' is for past.
    # But 'forecast' often has recent past. Let's try to fetch recent history.
    # For simplicity in this script, we might hit the archive endpoint if needed, 
    # but let's try the standard client first or just accept we get what the forecast endpoint gives (usually 1-2 days past).
    
    # Actually, for deep history we need the archive API. 
    # Let's stick to filling the "gap" if any, or just acknowledging the weather client 
    # in app/services/weather.py might need an update for 'archive' support.
    # For now, let's focus on PRICES which is the most important.
    pass

async def backfill_prices():
    print("Fetching historical Wholesale Prices (SMARD)...")
    client = SmardClient()
    db = SessionLocal()
    
    # SMARD API is a bit complex for history (requires specific file timestamps).
    # However, the standard endpoint often returns a good chunk of recent data.
    # Let's try to fetch what we can.
    
    market_data = await client.get_wholesale_prices()
    
    if "data" in market_data:
        count = 0
        for item in market_data["data"]:
            if item.get("price") is None:
                continue
                
            ts = datetime.fromtimestamp(item["timestamp"] / 1000.0)
            
            # Check if exists
            exists = db.query(DayAheadPrice).filter(
                DayAheadPrice.timestamp == ts,
                DayAheadPrice.zone == "DE-LU"
            ).first()
            
            if not exists:
                db_price = DayAheadPrice(
                    timestamp=ts,
                    price=item["price"],
                    currency="EUR",
                    zone="DE-LU"
                )
                db.add(db_price)
                count += 1
        
        db.commit()
        print(f"Successfully added {count} new price points to the database.")
    else:
        print("No data received from SMARD.")
    
    db.close()

if __name__ == "__main__":
    # Run the async loop
    asyncio.run(backfill_prices())
