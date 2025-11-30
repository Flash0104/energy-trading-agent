import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
import time

# Page Config
st.set_page_config(
    page_title="Energy Trading Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database Connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/energy_db")
AGENT_URL = os.getenv("AGENT_URL", "http://agent:8000")

@st.cache_resource
def get_db_engine():
    return create_engine(DB_URL)

def load_prices(start_dt, end_dt):
    engine = get_db_engine()
    query = f"""
    SELECT timestamp, price, zone 
    FROM dayahead_prices 
    WHERE timestamp BETWEEN '{start_dt}' AND '{end_dt}'
    ORDER BY timestamp ASC
    """
    return pd.read_sql(query, engine)

def load_news():
    engine = get_db_engine()
    query = "SELECT published, title, summary, url FROM energy_news ORDER BY published DESC LIMIT 20"
    return pd.read_sql(query, engine)

def load_weather(start_dt, end_dt):
    engine = get_db_engine()
    query = f"""
    SELECT timestamp, temperature, wind_speed, solar_radiation 
    FROM weather_data 
    WHERE timestamp BETWEEN '{start_dt}' AND '{end_dt}'
    ORDER BY timestamp ASC
    """
    return pd.read_sql(query, engine)

# --- Sidebar Filters ---
st.sidebar.title("🔍 Filters")

# "Current" button logic
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Live"

if st.sidebar.button("⚡ Show Live / Current", type="primary"):
    st.session_state.view_mode = "Live"

if st.session_state.view_mode == "Live":
    # Live View: Last 24h + Next 48h (Day Ahead)
    now = datetime.now()
    start_date = now - timedelta(hours=24)
    end_date = now + timedelta(hours=48)
    st.sidebar.info("Showing: Last 24h & Next 48h (Day-Ahead)")
else:
    # Custom Date Selection
    selected_date = st.sidebar.date_input("Select Date", datetime.now())
    start_date = datetime.combine(selected_date, datetime.min.time())
    end_date = datetime.combine(selected_date, datetime.max.time())

# Manual override if user picks a date
if st.sidebar.date_input("Or Pick a Date", value=None, key="date_picker"):
    st.session_state.view_mode = "Custom"
    d = st.session_state.date_picker
    start_date = datetime.combine(d, datetime.min.time())
    end_date = datetime.combine(d, datetime.max.time())

# --- UI Layout ---

st.title("⚡ Energy Trading Insight Agent")
st.markdown("### Real-time Market Data & AI Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📉 Market Prices (SMARD)")
    try:
        df_prices = load_prices(start_date, end_date)
        if not df_prices.empty:
            fig = px.line(df_prices, x='timestamp', y='price', color='zone', title='Day-Ahead Electricity Prices (€/MWh)')
            # Add a vertical line for "Now"
            fig.add_vline(x=datetime.now().timestamp() * 1000, line_width=1, line_dash="dash", line_color="red", annotation_text="Now")
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("ℹ️ **Note:** 'Day-Ahead' prices are auctioned for the next day. Seeing future data here is correct and expected.")
        else:
            st.info(f"No price data found for {start_date.date()}. Agent is fetching...")
    except Exception as e:
        st.error(f"Database Error: {e}")

    st.subheader("☀️ Weather Forecast (Renewables)")
    try:
        df_weather = load_weather(start_date, end_date)
        if not df_weather.empty:
            fig_w = px.line(df_weather, x='timestamp', y=['wind_speed', 'solar_radiation'], title='Wind (km/h) & Solar (W/m²) Forecast')
            st.plotly_chart(fig_w, use_container_width=True)
        else:
            st.info("No weather data available for this period.")
    except Exception as e:
        st.error(f"Database Error: {e}")

with col2:
    st.subheader("🤖 AI Trading Signal")
    
    analysis_type = st.radio("Select Analysis Source", ["Price Action (SMARD)", "Market Sentiment (News)", "Weather Impact (OpenMeteo)"])
    
    if st.button("Generate Live Insight", type="primary"):
        with st.spinner("Agent is analyzing market data..."):
            try:
                params = {}
                if st.session_state.view_mode == "Custom":
                    params["date"] = start_date.strftime("%Y-%m-%d")

                # --- Background Fetch: Weather ---
                try:
                    w_params = params.copy()
                    w_params["skip_analysis"] = "true"
                    requests.get(f"{AGENT_URL}/insights/weather", params=w_params, timeout=5)
                except Exception as e:
                    print(f"Weather fetch warning: {e}")

                # --- Main Analysis ---
                if "Price" in analysis_type:
                    endpoint = "/insights/smard"
                elif "News" in analysis_type:
                    endpoint = "/insights/news"
                else:
                    endpoint = "/insights/weather"
                
                response = requests.get(f"{AGENT_URL}{endpoint}", params=params)
                
                if response.status_code == 200:
                    # Save to Session State
                    st.session_state['last_insight'] = response.json()
                    st.session_state['last_insight_time'] = datetime.now().strftime("%H:%M:%S")
                    
                    # Force update to show new chart data
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Agent Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

    # --- Display Persisted Insight ---
    if 'last_insight' in st.session_state:
        data = st.session_state['last_insight']
        
        st.divider()
        st.caption(f"Last Updated: {st.session_state.get('last_insight_time', '')}")
        
        # Display Signal
        action = data.get("action", "HOLD")
        color = "green" if action == "BUY" else "red" if action == "SELL" else "gray"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: #1E1E1E; border-radius: 10px; border: 2px solid {color}; margin-bottom: 20px;">
            <h1 style="color: {color}; margin: 0;">{action}</h1>
            <p style="margin: 0; opacity: 0.8;">Confidence: {data.get('confidence', 0)*100:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Reasoning")
        for reason in data.get("reasoning", []):
            st.markdown(f"- {reason}")
            
        st.info(f"Summary: {data.get('summary')}")

st.divider()

st.subheader("📰 Latest Energy News (GDELT)")
try:
    df_news = load_news()
    if not df_news.empty:
        for index, row in df_news.iterrows():
            with st.expander(f"{row['published']} - {row['title']}"):
                st.write(row['summary'])
                st.markdown(f"[Read Source]({row['url']})")
    else:
        st.info("No news fetched yet.")
except Exception as e:
    st.error(f"Database Error: {e}")
