from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import os
import json
from openai import AsyncOpenAI

class TradingInsight(BaseModel):
    summary: str
    action: str  # e.g., "BUY", "SELL", "HOLD"
    confidence: float
    reasoning: List[str]
    data: Optional[Dict[str, Any]] = None

class EnergyAgent:
    """
    Agent that analyzes energy market data and generates trading insights.
    """
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def analyze(self, market_data: Dict[str, Any]) -> TradingInsight:
        """
        Analyze the provided market data and return a structured insight.
        """
        # If no API key, fallback to mock
        if not os.getenv("OPENAI_API_KEY"):
             prices = market_data.get("data", [])
             avg_price = sum(p.get("price", 0) for p in prices) / len(prices) if prices else 0
             return TradingInsight(
                summary=f"Analyzed {len(prices)} data points. Average price: {avg_price:.2f} (MOCK - Set OPENAI_API_KEY for real AI)",
                action="HOLD",
                confidence=0.5,
                reasoning=["No OpenAI API Key found.", "Using fallback logic."],
                data=market_data
            )

        prompt = f"""
        You are an expert Energy Trading AI. Analyze the following market data and provide a trading recommendation.
        
        Market Data:
        {json.dumps(market_data, default=str)}
        
        Provide your response in JSON format with the following keys:
        - summary: A brief summary of the market situation.
        - action: BUY, SELL, or HOLD.
        - confidence: A float between 0.0 and 1.0.
        - reasoning: A list of strings explaining your decision.
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Attach raw data to the result
            result["data"] = market_data
            
            return TradingInsight(**result)
            
        except Exception as e:
            return TradingInsight(
                summary=f"Error generating insight: {str(e)}",
                action="HOLD",
                confidence=0.0,
                reasoning=["AI generation failed."],
                data=market_data
            )
