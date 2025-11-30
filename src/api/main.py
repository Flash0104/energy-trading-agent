import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db, engine
from src.db.models import Base, DayAheadPrice, EnergyNews
from src.ingestion.entsoe import fetch_dayahead_prices
from src.ingestion.gdelt import fetch_energy_news
from src.agent.insights import run_agent_analysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Energy Trading Insight Agent API")

# Pydantic models for API
class InsightRequest(BaseModel):
    model: Optional[str] = "gpt-4o-mini"

class IngestionRequest(BaseModel):
    days: int = 1

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ingestion/entsoe")
def trigger_entsoe_ingestion(request: IngestionRequest, db: Session = Depends(get_db)):
    """
    Triggers ingestion of ENTSO-E Day-Ahead Prices.
    """
    try:
        end_date = datetime.utcnow() + timedelta(days=1) # Get tomorrow's prices too if available
        start_date = datetime.utcnow() - timedelta(days=request.days)
        
        prices_data = fetch_dayahead_prices(start_date, end_date)
        
        count = 0
        for p_data in prices_data:
            # Check if exists
            exists = db.query(DayAheadPrice).filter(
                DayAheadPrice.timestamp == p_data["timestamp"],
                DayAheadPrice.zone == p_data["zone"]
            ).first()
            
            if not exists:
                db_price = DayAheadPrice(
                    timestamp=p_data["timestamp"],
                    price=p_data["price"],
                    currency=p_data["currency"],
                    zone=p_data["zone"]
                )
                db.add(db_price)
                count += 1
        
        db.commit()
        return {"status": "success", "inserted_count": count}
        
    except Exception as e:
        logger.error(f"ENTSO-E ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/gdelt")
def trigger_gdelt_ingestion(request: IngestionRequest, db: Session = Depends(get_db)):
    """
    Triggers ingestion of GDELT Energy News.
    """
    try:
        news_data = fetch_energy_news(timespan=f"{request.days * 24}h")
        
        count = 0
        for n_data in news_data:
            # Check if exists by URL
            if n_data.get("url"):
                exists = db.query(EnergyNews).filter(EnergyNews.url == n_data["url"]).first()
                if exists:
                    continue
            
            db_news = EnergyNews(
                title=n_data["title"],
                summary=n_data["summary"],
                published=n_data["published"],
                url=n_data["url"]
                # Embedding generation would happen here or in a background task
                # For now we skip embedding generation to keep it simple as per prompt requirements regarding "Use pgvector if installed"
                # Ideally we would use an embedding model here.
            )
            db.add(db_news)
            count += 1
            
        db.commit()
        return {"status": "success", "inserted_count": count}
        
    except Exception as e:
        logger.error(f"GDELT ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/run")
def generate_insights(request: InsightRequest, db: Session = Depends(get_db)):
    """
    Generates trading insights using the AI Agent.
    """
    try:
        # We could pass the model from request to the agent if we updated the agent signature
        # For now, it uses the env var or default
        insights = run_agent_analysis(db)
        return insights
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prices/latest")
def get_latest_prices(limit: int = 24, db: Session = Depends(get_db)):
    prices = db.query(DayAheadPrice).order_by(DayAheadPrice.timestamp.desc()).limit(limit).all()
    return prices

@app.get("/news/latest")
def get_latest_news(limit: int = 10, db: Session = Depends(get_db)):
    news = db.query(EnergyNews).order_by(EnergyNews.published.desc()).limit(limit).all()
    return news
