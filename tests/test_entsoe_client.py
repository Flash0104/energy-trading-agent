import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from ingestion.entsoe_client import fetch_load_data, fetch_csv_data

def test_fetch_load():
    print("Testing fetch_load_data...")
    domain_code = "10Y1001A1001A82H" # DE-LU
    start_date = datetime(2025, 11, 23)
    end_date = datetime(2025, 11, 29, 23)
    
    try:
        df = fetch_load_data(domain_code, start_date, end_date)
        print("Load Data fetched successfully!")
        print(df.head())
        print(df.tail())
        print(f"Total rows: {len(df)}")
    except Exception as e:
        print(f"Error fetching load data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Body: {e.response.text}")

def test_fetch_prices_csv():
    print("\nTesting fetch_csv_data (Prices)...")
    domain_code = "10Y1001A1001A83F" # DE-LU
    
    try:
        # A44 = Price Document, A01 = Day Ahead
        df = fetch_csv_data("A44", "A01", domain_code)
        print("Price Data (CSV) fetched successfully!")
        print(df.head())
        print(f"Total rows: {len(df)}")
    except Exception as e:
        print(f"Error fetching price data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Body: {e.response.text}")

if __name__ == "__main__":
    test_fetch_load()
    test_fetch_prices_csv()
