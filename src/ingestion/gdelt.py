import httpx
from datetime import datetime
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

async def fetch_energy_news(
    query: str = "energy germany electricity gas emissions",
    max_records: int = 50,
    timespan: str = "24h"
) -> List[Dict]:
    """
    Fetches energy-related news from GDELT Project API.
    
    Args:
        query: Search query string
        max_records: Maximum number of records to return
        timespan: Time window (e.g., '24h', '1w')
        
    Returns:
        List of dictionaries containing news metadata.
    """
    
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": max_records,
        "timespan": timespan,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GDELT_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        if "articles" not in data:
            logger.warning("No articles found in GDELT response")
            return []
            
        return parse_gdelt_response(data["articles"])
        
    except Exception as e:
        logger.error(f"Error fetching data from GDELT: {e}")
        return []

def parse_gdelt_response(articles: List[Dict]) -> List[Dict]:
    """
    Parses GDELT articles and normalizes them.
    """
    news_items = []
    
    for article in articles:
        # GDELT returns dates like "20231027T103000Z"
        seendate = article.get("seendate")
        published_dt = None
        if seendate:
            try:
                published_dt = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ")
            except ValueError:
                logger.warning(f"Could not parse date: {seendate}")
        
        news_items.append({
            "title": article.get("title"),
            "url": article.get("url"),
            "published": published_dt,
            "summary": "", # GDELT ArtList mode doesn't always provide full summary, might need scraping or different mode
            "source": article.get("sourcegeography") or article.get("domain")
        })
        
    return news_items
