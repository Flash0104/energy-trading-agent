# ⚡ Energy Trading Insight Agent

An autonomous AI Agent that analyzes real-time energy market data, news, and weather forecasts to generate trading insights (BUY/SELL/HOLD).

## 🚀 Features

*   **Multi-Source Data Ingestion**:
    *   📉 **Market Prices**: SMARD API (German Wholesale Electricity Prices).
    *   📰 **Global News**: GDELT Project (Energy-related events).
    *   ☀️ **Weather**: Open-Meteo (Wind & Solar Forecasts).
*   **AI Analysis**: Powered by **OpenAI GPT-4o-mini** to synthesize complex data into actionable trading signals.
*   **Vector Database**: PostgreSQL with `pgvector` for storing data and future RAG capabilities.
*   **Interactive Dashboard**: Built with **Streamlit** for real-time visualization.
*   **Workflow Automation**: Orchestrated by **n8n** for scheduled analysis.
*   **Containerized**: Fully Dockerized for easy deployment.

## 🛠️ Tech Stack

*   **Language**: Python 3.11
*   **Backend**: FastAPI
*   **Frontend**: Streamlit
*   **Database**: PostgreSQL 16 (pgvector)
*   **Orchestration**: n8n
*   **Infrastructure**: Docker Compose, Hetzner Cloud

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/energy-trading-agent.git
    cd energy-trading-agent
    ```

2.  **Set up Environment Variables**:
    Copy `.env.example` to `.env` and fill in your keys:
    ```bash
    cp .env.example .env
    ```

3.  **Run with Docker**:
    ```bash
    docker compose up -d --build
    ```

4.  **Access the Services**:
    *   📊 **Dashboard**: `http://localhost:8501`
    *   ⚡ **n8n Workflows**: `http://localhost:5678`
    *   🗄️ **Database Admin**: `http://localhost:8080`
    *   🤖 **API Docs**: `http://localhost:8000/docs`

## 🏗️ Architecture

[Agent (FastAPI)] <--> [PostgreSQL (Data Store)]
       ^                       ^
       |                       |
[n8n (Orchestrator)]    [Streamlit (Dashboard)]
       |
[External APIs (SMARD, GDELT, OpenMeteo, OpenAI)]

## 📜 License

MIT
