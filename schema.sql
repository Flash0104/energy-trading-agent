-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Day-ahead electricity prices table
CREATE TABLE IF NOT EXISTS dayahead_prices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    price NUMERIC NOT NULL,
    currency TEXT DEFAULT 'EUR',
    zone TEXT DEFAULT 'DE-LU',
    UNIQUE(timestamp, zone)
);

-- Energy news table with vector embeddings
CREATE TABLE IF NOT EXISTS energy_news (
    id SERIAL PRIMARY KEY,
    title TEXT,
    summary TEXT,
    published TIMESTAMPTZ,
    url TEXT UNIQUE,
    embedding VECTOR(1536)
);

-- Index for faster vector similarity search (IVFFlat or HNSW)
-- Using HNSW for better performance/recall trade-off
CREATE INDEX IF NOT EXISTS energy_news_embedding_idx ON energy_news USING hnsw (embedding vector_cosine_ops);
