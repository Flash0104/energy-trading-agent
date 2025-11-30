import httpx
from typing import Dict, Any, Optional
import os

class ElexonClient:
    """
    Client for Elexon BMRS API.
    Docs: https://www.elexon.co.uk/guidance-note/bmrs-api-data-push-user-guide/
    """
    BASE_URL = "https://api.bmreports.com/BMRS"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEXON_API_KEY", "mock_key")

    async def get_system_prices(self) -> Dict[str, Any]:
        """
        Get System Buy/Sell Prices (SBP/SSP).
        Report: DERSYSDATA
        """
        if self.api_key == "mock_key":
             return {
                "error": "ELEXON_API_KEY is missing. Please provide a valid API key.",
                "source": "Elexon (Mock)"
            }
        
        try:
            # Fetch data for today
            today = datetime.utcnow().strftime("%Y-%m-%d")
            url = f"{self.BASE_URL}/DERSYSDATA/v1"
            params = {
                "APIKey": self.api_key,
                "ServiceType": "json",
                "SettlementDate": today
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            
            # Process the response
            # Structure: response -> responseBody -> responseList -> item (list)
            items = data.get("response", {}).get("responseBody", {}).get("responseList", {}).get("item", [])
            
            formatted_data = []
            for item in items:
                formatted_data.append({
                    "settlement_date": item.get("settlementDate"),
                    "settlement_period": item.get("settlementPeriod"),
                    "sbp": item.get("systemBuyPrice"),
                    "ssp": item.get("systemSellPrice")
                })
                
            return {
                "data": formatted_data[-48:], # Last 48 periods (approx 24 hours)
                "source": "Elexon (Real Data)",
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "source": "Elexon (Error)"}
