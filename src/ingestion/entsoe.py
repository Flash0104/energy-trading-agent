import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENTSOE_BASE_URL = "https://web-api.tp.entsoe.eu/api"

def fetch_dayahead_prices(
    start_date: datetime,
    end_date: datetime,
    security_token: Optional[str] = None,
    in_domain: str = "10Y1001A1001A83F", # DE-LU Bidding Zone
    out_domain: str = "10Y1001A1001A83F"
) -> List[Dict]:
    """
    Fetches Day-Ahead Prices from ENTSO-E Transparency Platform.
    
    Args:
        start_date: Start datetime (UTC)
        end_date: End datetime (UTC)
        security_token: ENTSO-E API Token (defaults to env var ENTSOE_SECURITY_TOKEN)
        in_domain: EIC code for the bidding zone (default DE-LU)
        out_domain: EIC code for the bidding zone (default DE-LU)
        
    Returns:
        List of dictionaries containing normalized price data.
    """
    token = security_token or os.getenv("ENTSOE_SECURITY_TOKEN")
    if not token:
        raise ValueError("ENTSOE_SECURITY_TOKEN not found in environment variables or arguments.")

    # Format dates to YYYYMMDDHHMM
    period_start = start_date.strftime("%Y%m%d%H%M")
    period_end = end_date.strftime("%Y%m%d%H%M")

    params = {
        "securityToken": token,
        "documentType": "A44",  # Price Document
        "in_Domain": in_domain,
        "out_Domain": out_domain,
        "periodStart": period_start,
        "periodEnd": period_end
    }

    try:
        response = requests.get(ENTSOE_BASE_URL, params=params)
        response.raise_for_status()
        
        return parse_entsoe_xml(response.content)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from ENTSO-E: {e}")
        if response is not None:
            logger.error(f"Response content: {response.text}")
        raise

def parse_entsoe_xml(xml_content: bytes) -> List[Dict]:
    """
    Parses ENTSO-E XML response and extracts price data.
    """
    ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        raise

    prices = []
    
    # Iterate through TimeSeries
    for time_series in root.findall('.//ns:TimeSeries', ns):
        currency = time_series.find('ns:currency_Unit.name', ns).text
        measure_unit = time_series.find('ns:price_Measure_Unit.name', ns).text
        
        period = time_series.find('ns:Period', ns)
        if period is None:
            continue
            
        start_str = period.find('ns:timeInterval/ns:start', ns).text
        end_str = period.find('ns:timeInterval/ns:end', ns).text
        resolution = period.find('ns:resolution', ns).text
        
        # Parse start time (ISO 8601)
        # Note: This is a simplified parser. Production might need isodate or similar.
        # ENTSO-E usually returns UTC like 2023-10-26T22:00Z
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        
        for point in period.findall('ns:Point', ns):
            position = int(point.find('ns:position', ns).text)
            price_amount = float(point.find('ns:price.amount', ns).text)
            
            # Calculate timestamp based on resolution and position
            # PT60M = 60 minutes
            if resolution == 'PT60M':
                point_time = start_dt + timedelta(hours=position - 1)
            elif resolution == 'PT15M':
                point_time = start_dt + timedelta(minutes=(position - 1) * 15)
            else:
                # Fallback or other resolutions
                point_time = start_dt + timedelta(hours=position - 1)

            prices.append({
                "timestamp": point_time,
                "price": price_amount,
                "currency": currency,
                "unit": measure_unit,
                "zone": "DE-LU" # Hardcoded for this specific task context
            })
            
    return prices
