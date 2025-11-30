import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class SmardClient:
    """
    Client for the SMARD (Bundesnetzagentur) API.
    Docs: https://www.smard.de/en/download-center/download-market-data
    """
    BASE_URL = "https://www.smard.de/app/chart_data"

    async def get_market_data(self, filter_id: int, region_id: str, resolution: str = "hour") -> Dict[str, Any]:
        """
        Fetch market data from SMARD.
        
        Args:
            filter_id: The ID of the data category (e.g., 1223 for Wholesale Prices)
            region_id: The region ID (e.g., 'DE-LU' for Germany/Luxembourg)
            resolution: Time resolution (e.g., 'hour', 'quarter_hour')
        """
        # Note: SMARD API structure is a bit complex with timestamps. 
        # This is a simplified implementation for the PoC.
        # Real implementation would need to handle the specific timestamp directory structure of SMARD.
        
        # For now, we will mock the response structure or implement a basic fetch if we had the exact endpoint.
        # SMARD uses a structure like: /<filter_id>/<region>/<resolution>/<timestamp>.json
        
        # Let's implement a generic fetcher that assumes we know the timestamp
        # In a real agent, we would list available timestamps first.
        
        return {"status": "not_implemented_fully", "message": "SMARD API requires complex timestamp handling"}

    async def get_wholesale_prices(self, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get wholesale electricity prices for Germany/Luxembourg.
        Filter ID: 4169 (Wholesale prices)
        Region: DE-LU
        Resolution: hour
        """
        filter_id = 4169
        region = "DE-LU"
        resolution = "hour"
        
        try:
            # 1. Get the index to find available timestamps
            index_url = f"{self.BASE_URL}/{filter_id}/{region}/index_{resolution}.json"
            async with httpx.AsyncClient() as client:
                resp = await client.get(index_url)
                resp.raise_for_status()
                timestamps = resp.json().get("timestamps", [])
            
            if not timestamps:
                return {"error": "No data available from SMARD"}
            
            # 2. Get the latest timestamp
            latest_ts = timestamps[-1]
            
            # 3. Fetch the actual data
            data_url = f"{self.BASE_URL}/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{latest_ts}.json"
            async with httpx.AsyncClient() as client:
                resp = await client.get(data_url)
                resp.raise_for_status()
                data = resp.json()
            
            # 4. Process the data
            series = data.get("series", [])
            formatted_data = []
            for point in series:
                # point is [timestamp, value]
                formatted_data.append({
                    "timestamp": point[0],
                    "price": point[1]
                })
                
            # Return only the last 24 hours to keep it relevant
            return {
                "data": formatted_data[-24:],
                "source": "SMARD (Real Data)",
                "region": region,
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "source": "SMARD (Error)"}

    async def get_historical_prices(self, target_date: datetime) -> Dict[str, Any]:
        """
        Get wholesale prices for a specific date.
        """
        filter_id = 4169
        region = "DE-LU"
        resolution = "hour"
        
        try:
            # 1. Get the index
            index_url = f"{self.BASE_URL}/{filter_id}/{region}/index_{resolution}.json"
            async with httpx.AsyncClient() as client:
                resp = await client.get(index_url)
                resp.raise_for_status()
                timestamps = resp.json().get("timestamps", [])
            
            if not timestamps:
                return {"error": "No data available"}

            # 2. Find the best timestamp file
            # SMARD timestamps in index are the start of the file's data range.
            # We need to find the timestamp <= target_date_ts
            target_ts = int(target_date.timestamp() * 1000)
            selected_ts = None
            
            # Timestamps are sorted. We want the largest timestamp that is <= target_ts
            for ts in timestamps:
                if ts <= target_ts:
                    selected_ts = ts
                else:
                    break
            
            if not selected_ts:
                selected_ts = timestamps[0] # Fallback to oldest

            # 3. Fetch data
            data_url = f"{self.BASE_URL}/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{selected_ts}.json"
            async with httpx.AsyncClient() as client:
                resp = await client.get(data_url)
                resp.raise_for_status()
                data = resp.json()

            # 4. Filter for the specific date
            series = data.get("series", [])
            formatted_data = []
            
            # Define start/end of the target day
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            ts_start = int(day_start.timestamp() * 1000)
            ts_end = int(day_end.timestamp() * 1000)

            for point in series:
                ts = point[0]
                val = point[1]
                if ts_start <= ts < ts_end:
                    formatted_data.append({
                        "timestamp": ts,
                        "price": val
                    })
            
            return {
                "data": formatted_data,
                "source": "SMARD (History)",
                "region": region
            }

        except Exception as e:
            return {"error": str(e)}
