# System Architecture

## Overview

The Energy Trading Insight Agent System (ATIA) is a modular microservices-based application designed to provide AI-driven insights for energy trading.

## Components

### 1. Data Ingestion Layer
- **ENTSO-E Module**: Connects to the ENTSO-E Transparency Platform API to fetch Day-Ahead Electricity Prices for the DE-LU bidding zone.
- **GDELT Module**: Queries the GDELT Project API for real-time news related to energy, electricity, gas, and emissions in Germany.

### 2. Database Layer
- **PostgreSQL**: Primary data store.
- **pgvector**: Extension for storing and searching vector embeddings of news articles (for future RAG capabilities).
- **Schema**:
  - `dayahead_prices`: Stores timestamped price data.
  - `energy_news`: Stores news metadata and embeddings.

### 3. AI Agent Layer
- **Logic**: Python-based agent that retrieves recent data from the database.
- **LLM**: Uses OpenAI's GPT-4o-mini to analyze the data and generate structured JSON insights.
- **Prompting**: Uses a specialized system prompt to enforce a trading-style persona and output format.

### 4. API Layer
- **FastAPI**: Exposes the system functionality via HTTP endpoints.
- **Endpoints**:
  - `/ingestion/*`: Triggers data fetching.
  - `/insights/run`: Invokes the agent.
  - `/prices/latest` & `/news/latest`: Data access.

### 5. Automation Layer
- **n8n**: Workflow automation tool.
- **Workflow**:
  1. **Webhook Trigger**: Accepts external requests.
  2. **Ingest ENTSO-E**: Calls API to fetch prices.
  3. **Ingest GDELT**: Calls API to fetch news.
  4. **Generate Insights**: Calls API to run the agent.
  5. **Response**: Returns the generated insights.

## Deployment

- **Docker Compose**: Orchestrates the services (API, Postgres, n8n).
- **Network**: All services communicate via a private Docker bridge network (`atia-network`).
- **Volumes**: Persistent storage for Postgres data and n8n configuration.

## Data Flow

1. **Trigger**: n8n Webhook or manual API call.
2. **Ingestion**: API calls Ingestion Modules -> External APIs -> Database.
3. **Analysis**: API calls Agent -> Database (Fetch Data) -> OpenAI API (Generate Insight).
4. **Output**: JSON Insight Report.
