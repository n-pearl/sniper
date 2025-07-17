-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sniper_user') THEN
        CREATE USER sniper_user WITH PASSWORD 'sniper_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sniper TO sniper_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sniper_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sniper_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sniper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES IN SCHEMA public TO sniper_user;

-- Create news_articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID DEFAULT gen_random_uuid(),
    published_at TIMESTAMP NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    url VARCHAR(1000) NOT NULL,
    source VARCHAR(100) NOT NULL,
    author VARCHAR(200),
    ticker_symbol VARCHAR(10),
    company_name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    confidence_score FLOAT,
    sentiment_vector vector(768),
    content_vector vector(1536),
    keywords JSONB,
    entities JSONB,
    market_impact_score FLOAT,
    is_processed BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    raw_data JSONB,
    PRIMARY KEY (id, published_at)
);

-- Create sentiment_analyses table
CREATE TABLE IF NOT EXISTS sentiment_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id UUID NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    sentiment_score FLOAT NOT NULL,
    sentiment_label VARCHAR(20) NOT NULL,
    confidence_score FLOAT,
    embedding_vector vector(768),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data JSONB
);

-- Create market_impacts table
CREATE TABLE IF NOT EXISTS market_impacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id UUID NOT NULL,
    ticker_symbol VARCHAR(10) NOT NULL,
    price_before FLOAT,
    price_after FLOAT,
    price_change_percent FLOAT,
    volume_change_percent FLOAT,
    impact_window_hours INTEGER NOT NULL DEFAULT 24,
    measurement_time TIMESTAMP NOT NULL,
    sentiment_price_correlation FLOAT,
    impact_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_news_articles_published_ticker ON news_articles(published_at, ticker_symbol);
CREATE INDEX IF NOT EXISTS idx_news_articles_sentiment_published ON news_articles(sentiment_score, published_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON news_articles(url);
CREATE INDEX IF NOT EXISTS idx_news_articles_title ON news_articles(title);
CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_article_model ON sentiment_analyses(article_id, model_name);
CREATE INDEX IF NOT EXISTS idx_market_impacts_ticker_time ON market_impacts(ticker_symbol, measurement_time);

-- Convert to TimescaleDB hypertable for time-series data
SELECT create_hypertable('news_articles', 'published_at', if_not_exists => TRUE); 