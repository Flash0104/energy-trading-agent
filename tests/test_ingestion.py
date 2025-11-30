import pytest
from datetime import datetime
from src.ingestion.entsoe import parse_entsoe_xml
from src.ingestion.gdelt import parse_gdelt_response

def test_parse_entsoe_xml():
    # Minimal mock XML
    xml_content = b"""
    <Publication_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0">
        <TimeSeries>
            <currency_Unit.name>EUR</currency_Unit.name>
            <price_Measure_Unit.name>MWH</price_Measure_Unit.name>
            <Period>
                <timeInterval>
                    <start>2023-10-26T22:00Z</start>
                    <end>2023-10-27T22:00Z</end>
                </timeInterval>
                <resolution>PT60M</resolution>
                <Point>
                    <position>1</position>
                    <price.amount>10.5</price.amount>
                </Point>
            </Period>
        </TimeSeries>
    </Publication_MarketDocument>
    """
    prices = parse_entsoe_xml(xml_content)
    assert len(prices) == 1
    assert prices[0]['price'] == 10.5
    assert prices[0]['currency'] == 'EUR'
    assert prices[0]['zone'] == 'DE-LU'

def test_parse_gdelt_response():
    mock_articles = [
        {
            "title": "Energy Crisis",
            "url": "http://example.com",
            "seendate": "20231027T103000Z",
            "domain": "example.com"
        }
    ]
    news = parse_gdelt_response(mock_articles)
    assert len(news) == 1
    assert news[0]['title'] == "Energy Crisis"
    assert news[0]['published'] == datetime(2023, 10, 27, 10, 30, 0)
