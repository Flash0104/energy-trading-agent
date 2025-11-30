import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from io import StringIO
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENTSOE_API_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_FILE_SERVICE_URL = "https://web-api.tp.entsoe.eu/file-service/data"

# Browser-like headers to mimic the frontend
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://transparency.entsoe.eu/",
    "Origin": "https://transparency.entsoe.eu",
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_load_data(
    domain_code: str,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """
    Fetches load data from ENTSO-E backend (XML endpoint).
    
    Args:
        domain_code: EIC code for the bidding zone (e.g., '10Y1001A1001A82H' for DE-LU Load)
        start_date: Start datetime
        end_date: End datetime
        
    Returns:
        pd.DataFrame with columns ['timestamp', 'MW']
    """
    # Format dates to YYYYMMDDHHMM
    period_start = start_date.strftime("%Y%m%d%H%M")
    period_end = end_date.strftime("%Y%m%d%H%M")
    
    params = {
        "documentType": "A65",  # System Total Load
        "processType": "A16",   # Realised
        "in_Domain": domain_code,
        "periodStart": period_start,
        "periodEnd": period_end
    }
    
    logger.info(f"Fetching load data for {domain_code} from {period_start} to {period_end}")
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(ENTSOE_API_URL, params=params)
        response.raise_for_status()
        
        return _parse_load_xml(response.content)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching load data: {e}")
        if 'response' in locals() and response is not None:
             logger.error(f"Response content: {response.text[:500]}...") # Log first 500 chars
        raise

def _parse_load_xml(xml_content: bytes) -> pd.DataFrame:
    """
    Parses ENTSO-E XML response for Load Data.
    """
    # ENTSO-E XML uses namespaces. We need to handle them.
    # The namespace URI might change versions, but usually follows a pattern.
    # We'll try to extract it or handle it generically.
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        raise

    # Extract namespace from root tag
    # e.g. {urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}Publication_MarketDocument
    if '}' in root.tag:
        ns_url = root.tag.split('}')[0].strip('{')
        ns = {'ns': ns_url}
    else:
        ns = {}

    data = []
    
    # Find all TimeSeries
    # If ns is present, use it.
    time_series_list = root.findall('.//ns:TimeSeries', ns) if ns else root.findall('.//TimeSeries')
    
    for ts in time_series_list:
        # Check if it's the right object aggregation (optional, but good for safety)
        # For Load, we expect System Total Load
        
        period = ts.find('ns:Period', ns) if ns else ts.find('Period')
        if period is None:
            continue
            
        start_str = period.find('ns:timeInterval/ns:start', ns).text if ns else period.find('timeInterval/start').text
        resolution = period.find('ns:resolution', ns).text if ns else period.find('resolution').text
        
        # Parse start time. ENTSO-E usually returns UTC ISO format like 2023-10-26T22:00Z
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        
        points = period.findall('ns:Point', ns) if ns else period.findall('Point')
        
        for point in points:
            position = int(point.find('ns:position', ns).text if ns else point.find('position').text)
            quantity = float(point.find('ns:quantity', ns).text if ns else point.find('quantity').text)
            
            # Calculate timestamp
            if resolution == 'PT60M':
                point_time = start_dt + timedelta(hours=position - 1)
            elif resolution == 'PT15M':
                point_time = start_dt + timedelta(minutes=(position - 1) * 15)
            elif resolution == 'PT30M':
                point_time = start_dt + timedelta(minutes=(position - 1) * 30)
            else:
                # Fallback, assume 1 hour if unknown (risky but better than crash)
                logger.warning(f"Unknown resolution {resolution}, assuming 1 hour")
                point_time = start_dt + timedelta(hours=position - 1)
                
            data.append({
                'timestamp': point_time,
                'MW': quantity
            })
            
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values('timestamp').reset_index(drop=True)
        
    return df

def fetch_csv_data(
    document_type: str,
    process_type: str,
    domain_code: str,
    domain_param_name: str = "outBiddingZone_Domain"
) -> pd.DataFrame:
    """
    Fetches data from ENTSO-E File Service (CSV endpoint).
    Useful for Day-Ahead Prices (A44/A01) which works anonymously via this endpoint.
    
    Args:
        document_type: e.g., 'A44' (Price Document), 'A65' (Load)
        process_type: e.g., 'A01' (Day Ahead), 'A16' (Realised)
        domain_code: EIC code
        domain_param_name: The parameter name for the domain. 
                           For Prices it's usually 'outBiddingZone_Domain'.
                           For Load it might be 'outBiddingZone_Domain' or 'in_Domain' depending on the file service config,
                           but usually file service exports by bidding zone.
                           
    Returns:
        pd.DataFrame
    """
    params = {
        "documentType": document_type,
        "processType": process_type,
        domain_param_name: domain_code
    }
    
    logger.info(f"Fetching CSV data: {params}")
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(ENTSOE_FILE_SERVICE_URL, params=params)
        response.raise_for_status()
        
        # The response is a CSV file content
        csv_content = response.content.decode('utf-8')
        
        # Parse CSV
        df = pd.read_csv(StringIO(csv_content))
        
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching CSV data: {e}")
        raise

def merge_datasets(load_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges Load and Price datasets on timestamp.
    Assumes price_df has been processed to have a 'timestamp' column similar to load_df.
    """
    # This is a placeholder/helper. Real usage depends on the exact structure of price_df from CSV.
    # The CSV from file service usually has 'MTU' (Market Time Unit) which needs parsing.
    
    # For now, we just return an outer join if both have 'timestamp'
    if 'timestamp' in load_df.columns and 'timestamp' in price_df.columns:
        return pd.merge(load_df, price_df, on='timestamp', how='outer')
    
    return pd.DataFrame()
