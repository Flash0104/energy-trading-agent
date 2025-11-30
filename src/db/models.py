from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class DayAheadPrice(Base):
    __tablename__ = 'dayahead_prices'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, unique=True)
    price = Column(Numeric, nullable=False)
    currency = Column(String, default='EUR')
    zone = Column(String, default='DE-LU')

class EnergyNews(Base):
    __tablename__ = 'energy_news'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    summary = Column(Text)
    url = Column(String, unique=True)
    published = Column(DateTime(timezone=True))
    embedding = Column(Vector(1536))  # For OpenAI embeddings

class WeatherData(Base):
    __tablename__ = 'weather_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, unique=True)
    temperature = Column(Numeric)  # Celsius
    wind_speed = Column(Numeric)   # km/h
    solar_radiation = Column(Numeric) # W/m²
    zone = Column(String, default='DE')
