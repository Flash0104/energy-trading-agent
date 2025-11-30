from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.services.smard import SmardClient
from app.services.elexon import ElexonClient
from app.services.weather import WeatherClient
from app.agent import EnergyAgent, TradingInsight

from src.db.database import get_db, engine
from src.db.models import Base, DayAheadPrice, EnergyNews, WeatherData
from src.ingestion.gdelt import fetch_energy_news

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Energy Trading Insight Agent")

smard_client = SmardClient()
elexon_client = ElexonClient()
weather_client = WeatherClient()
agent = EnergyAgent()

@app.get("/insights/weather")
async def get_weather_insights(date: Optional[str] = None, skip_analysis: bool = False, db: Session = Depends(get_db)):
    # 1. Fetch Data
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        # Use Archive for past dates, Forecast for today/future
        if target_date.date() < datetime.now().date():
            forecast = await weather_client.get_historical_weather(target_date)
        else:
            forecast = await weather_client.get_forecast()
    else:
        forecast = await weather_client.get_forecast()
    
    # 2. Save to Database
    hourly = forecast.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    winds = hourly.get("wind_speed_10m", [])
    solars = hourly.get("direct_radiation", [])
    
    saved_data = []
    
    for i, t_str in enumerate(times):
        # OpenMeteo returns ISO string "2023-11-30T14:00"
        ts = datetime.fromisoformat(t_str)
        
        exists = db.query(WeatherData).filter(WeatherData.timestamp == ts).first()
        if not exists:
            wd = WeatherData(
                timestamp=ts,
                temperature=temps[i],
                wind_speed=winds[i],
                solar_radiation=solars[i],
                zone="DE"
            )
            db.add(wd)
            saved_data.append({
                "timestamp": t_str,
                "temp": temps[i],
                "wind": winds[i],
                "solar": solars[i]
            })
            
    db.commit()
    
    if skip_analysis:
        return {"status": "data_fetched", "count": len(saved_data)}
    
    # 3. Analyze
    if date:
        # Fetch specific date from DB
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_dt = target_date
        end_dt = target_date + timedelta(days=1)
        db_data = db.query(WeatherData).filter(
            WeatherData.timestamp >= start_dt, 
            WeatherData.timestamp < end_dt
        ).all()
    else:
        # Fetch last 24h from DB
        past_24h = datetime.now() - timedelta(hours=24)
        db_data = db.query(WeatherData).filter(WeatherData.timestamp >= past_24h).all()

    saved_data = [{
        "timestamp": d.timestamp.isoformat(),
        "temp": float(d.temperature),
        "wind": float(d.wind_speed),
        "solar": float(d.solar_radiation)
    } for d in db_data]

    analysis_input = {
        "source": "OpenMeteo (Weather)",
        "data": saved_data
    }
    
    return await agent.analyze(analysis_input)

@app.get("/")
async def root():
    return {"message": "Energy Trading Insight Agent is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/insights/smard", response_model=TradingInsight)
async def get_smard_insights(date: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch data from SMARD, save to DB, and generate trading insights.
    Optionally provide a 'date' (YYYY-MM-DD) to fetch historical data for that day.
    """
    try:
        # 1. Fetch Data
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            market_data = await smard_client.get_historical_prices(target_date)
        else:
            market_data = await smard_client.get_wholesale_prices()
        
        # 2. Save to Database and Filter Data for Agent
        valid_data = []
        if "data" in market_data:
            for item in market_data["data"]:
                # Skip if price is None
                if item.get("price") is None:
                    continue

                valid_data.append(item)

                # Convert timestamp (ms) to datetime
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
            db.commit()

        # 3. Fetch data for Analysis (Last 24h OR Specific Date)
        if date:
            # If historical, analyze that specific day
            target_date = datetime.strptime(date, "%Y-%m-%d")
            start_dt = target_date
            end_dt = target_date + timedelta(days=1)
            
            db_prices = db.query(DayAheadPrice).filter(
                DayAheadPrice.timestamp >= start_dt,
                DayAheadPrice.timestamp < end_dt,
                DayAheadPrice.zone == "DE-LU"
            ).order_by(DayAheadPrice.timestamp.asc()).all()
        else:
            # Default: Last 24h
            past_24h = datetime.now() - timedelta(hours=24)
            db_prices = db.query(DayAheadPrice).filter(
                DayAheadPrice.timestamp >= past_24h,
                DayAheadPrice.zone == "DE-LU"
            ).order_by(DayAheadPrice.timestamp.asc()).all()

        # Format for AI
        analysis_data = {
            "source": "database",
            "data": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "price": float(p.price)
                }
                for p in db_prices
            ]
        }

        # 4. Analyze with Agent
        insight = await agent.analyze(analysis_data)
        
        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/elexon", response_model=TradingInsight)
async def get_elexon_insights(db: Session = Depends(get_db)):
    """
    Fetch data from Elexon, save to DB, and generate trading insights.
    """
    try:
        market_data = await elexon_client.get_system_prices()
        
        # Save to Database
        if "data" in market_data:
            for item in market_data["data"]:
                # item has settlement_date (YYYY-MM-DD) and settlement_period (1-48)
                date_str = item["settlement_date"]
                period = int(item["settlement_period"])
                
                # Calculate timestamp
                # Period 1: 00:00 - 00:30
                base_date = datetime.strptime(date_str, "%Y-%m-%d")
                ts = base_date + timedelta(minutes=(period - 1) * 30)
                
                # Use System Buy Price (sbp) as the reference price
                price = item.get("sbp", 0)
                
                # Check if exists
                exists = db.query(DayAheadPrice).filter(
                    DayAheadPrice.timestamp == ts,
                    DayAheadPrice.zone == "GB"
                ).first()
                
                if not exists:
                    db_price = DayAheadPrice(
                        timestamp=ts,
                        price=price,
                        currency="GBP",
                        zone="GB"
                    )
                    db.add(db_price)
            db.commit()

        insight = await agent.analyze(market_data)
        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/news", response_model=TradingInsight)
async def get_news_insights(db: Session = Depends(get_db)):
    """
    Fetch news from GDELT, save to DB, and generate trading insights.
    """
    try:
        # 1. Fetch News
        news_items = await fetch_energy_news()
        
        # 2. Save to Database
        saved_count = 0
        for item in news_items:
            # Check if exists
            exists = db.query(EnergyNews).filter(EnergyNews.url == item["url"]).first()
            if not exists:
                db_news = EnergyNews(
                    title=item["title"],
                    summary=item["summary"],
                    published=item["published"],
                    url=item["url"]
                )
                db.add(db_news)
                saved_count += 1
        db.commit()
        
        # 3. Analyze with Agent
        market_data = {
            "type": "news",
            "count": len(news_items),
            "new_items": saved_count,
            "headlines": [item["title"] for item in news_items[:10]]
        }
        
        insight = await agent.analyze(market_data)
        return insight
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
