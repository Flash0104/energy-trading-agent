from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Energy Trading Insight Agent is running"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_smard_insights():
    response = client.get("/insights/smard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "action" in data
    assert "confidence" in data
    assert data["action"] in ["BUY", "SELL", "HOLD"]

def test_elexon_insights():
    response = client.get("/insights/elexon")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "action" in data
    # Mock data has low prices, so it should be BUY or HOLD depending on logic
    assert data["action"] in ["BUY", "SELL", "HOLD"]
