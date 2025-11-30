import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from openai import OpenAI

from src.db.models import DayAheadPrice, EnergyNews

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", model)

    def get_recent_data(self, db: Session, hours: int = 24) -> Dict:
        """
        Fetches recent prices and news from the database.
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Fetch prices
        prices = db.query(DayAheadPrice).filter(
            DayAheadPrice.timestamp >= since
        ).order_by(DayAheadPrice.timestamp.asc()).all()
        
        # Fetch news
        news = db.query(EnergyNews).filter(
            EnergyNews.published >= since
        ).order_by(EnergyNews.published.desc()).limit(10).all()
        
        return {
            "prices": [
                {"time": p.timestamp.isoformat(), "price": float(p.price), "currency": p.currency}
                for p in prices
            ],
            "news": [
                {"title": n.title, "summary": n.summary, "date": n.published.isoformat() if n.published else None}
                for n in news
            ]
        }

    def generate_insights(self, db: Session) -> Dict:
        """
        Generates trading insights based on recent data.
        """
        data = self.get_recent_data(db)
        
        if not data["prices"] and not data["news"]:
            logger.warning("No recent data found for insights generation.")
            return {
                "error": "Insufficient data",
                "market_summary": [],
                "risks": [],
                "opportunities": [],
                "news_sentiment": "neutral",
                "recommendation": "Hold (Insufficient Data)"
            }

        system_prompt = (
            "You are an AI assistant supporting a European energy trading desk.\n"
            "You receive electricity price data (DE-LU zone) and energy-related news.\n"
            "Produce a concise, factual, trading-style insight report.\n"
            "Output pure JSON only."
        )
        
        user_prompt = f"""
        Analyze the following data and provide trading insights:
        
        Recent Day-Ahead Prices (DE-LU):
        {json.dumps(data['prices'], indent=2)}
        
        Recent Energy News:
        {json.dumps(data['news'], indent=2)}
        
        Return a JSON object with the following structure:
        {{
          "market_summary": [...max 5 bullets],
          "risks": [...],
          "opportunities": [...],
          "news_sentiment": "positive" | "neutral" | "negative",
          "recommendation": "string"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise

def run_agent_analysis(db: Session) -> Dict:
    """
    Convenience function to run the agent.
    """
    agent = TradingAgent()
    return agent.generate_insights(db)
