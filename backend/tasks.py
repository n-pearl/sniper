from celery import Celery
from config import settings
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "sniper",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Import services after Celery app creation
from sentiment.sentiment_engine import sentiment_engine


def fetch_news_articles_sync(ticker_symbols: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Synchronous version of news fetching for Celery tasks
    """
    if not settings.ALPHA_VANTAGE_API_KEY:
        logger.error("Alpha Vantage API key not configured")
        return []
    
    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
            "limit": limit
        }
        
        if ticker_symbols:
            params["tickers"] = ",".join(ticker_symbols)
        
        # Use synchronous httpx client
        with httpx.Client(timeout=30.0) as client:
            response = client.get("https://www.alphavantage.co/query", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "feed" not in data:
                logger.warning("No news feed found in response")
                return []
            
            return data["feed"]
            
    except Exception as e:
        logger.error(f"Failed to fetch news articles: {e}")
        return []


@celery_app.task(bind=True, name="process_news_articles")
def process_news_articles(self, ticker_symbols: Optional[List[str]] = None, limit: int = 50):
    """
    Process news articles for given ticker symbols
    """
    try:
        logger.info(f"Starting news processing task for tickers: {ticker_symbols}")
        
        # Fetch news articles synchronously
        articles_data = fetch_news_articles_sync(ticker_symbols, limit)
        
        logger.info(f"Fetched {len(articles_data)} articles")
        
        # Process each article
        processed_count = 0
        for article_data in articles_data:
            try:
                # Analyze sentiment
                sentiment_result = analyze_article_sentiment.delay(article_data)
                processed_count += 1
                
                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': processed_count, 'total': len(articles_data)}
                )
                
            except Exception as e:
                logger.error(f"Error processing article {article_data.get('title', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Successfully queued {processed_count} articles for sentiment analysis")
        return {
            'status': 'completed',
            'articles_processed': processed_count,
            'total_articles': len(articles_data)
        }
        
    except Exception as e:
        logger.error(f"Error in process_news_articles task: {e}")
        raise


@celery_app.task(bind=True, name="analyze_article_sentiment")
def analyze_article_sentiment(self, article_data: Dict[str, Any]):
    """
    Analyze sentiment for a single news article
    """
    try:
        logger.info(f"Analyzing sentiment for article: {article_data.get('title', 'Unknown')}")
        
        # Initialize sentiment engine
        asyncio.run(sentiment_engine.initialize())
        
        # Extract text for analysis
        text = article_data.get('summary', '')
        if not text:
            text = article_data.get('title', '')
        
        # Analyze sentiment using FinBERT
        sentiment_result = asyncio.run(sentiment_engine.analyze_finbert(text))
        
        # Store results in database
        from backend.database import SessionLocal
        from models.news_models import NewsArticle
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # Parse published time
            published_at_str = article_data.get('time_published', '')
            if published_at_str:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            else:
                published_at = datetime.utcnow()
            
            # Update or create article with sentiment data
            article = db.query(NewsArticle).filter(
                NewsArticle.url == article_data.get('url')
            ).first()
            
            if article:
                article.sentiment_score = sentiment_result.get('sentiment_score')
                article.sentiment_label = sentiment_result.get('sentiment_label')
                article.confidence_score = sentiment_result.get('confidence_score')
                article.is_processed = True
                article.updated_at = datetime.utcnow()
            else:
                # Create new article
                article = NewsArticle(
                    title=article_data.get('title'),
                    content=article_data.get('summary'),
                    url=article_data.get('url'),
                    source=article_data.get('source'),
                    author=article_data.get('authors'),
                    ticker_symbol=article_data.get('ticker_sentiment', [{}])[0].get('ticker') if article_data.get('ticker_sentiment') else None,
                    published_at=published_at,
                    sentiment_score=sentiment_result.get('sentiment_score'),
                    sentiment_label=sentiment_result.get('sentiment_label'),
                    confidence_score=sentiment_result.get('confidence_score'),
                    is_processed=True,
                    raw_data=article_data
                )
                db.add(article)
            
            db.commit()
            logger.info(f"Successfully processed article: {article_data.get('title', 'Unknown')}")
            
            return {
                'status': 'completed',
                'article_id': str(article.id),
                'sentiment_score': sentiment_result.get('sentiment_score'),
                'sentiment_label': sentiment_result.get('sentiment_label')
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in analyze_article_sentiment task: {e}")
        raise


@celery_app.task(name="cleanup_old_articles")
def cleanup_old_articles(days_old: int = 30):
    """
    Clean up old articles from the database
    """
    try:
        logger.info(f"Starting cleanup of articles older than {days_old} days")
        
        from backend.database import SessionLocal
        from models.news_models import NewsArticle
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db = SessionLocal()
        try:
            # Mark old articles as archived
            old_articles = db.query(NewsArticle).filter(
                NewsArticle.published_at < cutoff_date,
                NewsArticle.is_archived == False
            ).all()
            
            for article in old_articles:
                article.is_archived = True
                article.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Archived {len(old_articles)} old articles")
            
            return {
                'status': 'completed',
                'articles_archived': len(old_articles)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_articles task: {e}")
        raise


@celery_app.task(name="update_market_data")
def update_market_data(ticker_symbols: Optional[List[str]] = None):
    """
    Update market data for given ticker symbols
    """
    try:
        logger.info(f"Starting market data update for tickers: {ticker_symbols}")
        
        # This would integrate with Alpha Vantage API
        # For now, just log the task
        logger.info("Market data update task completed")
        
        return {
            'status': 'completed',
            'tickers_updated': len(ticker_symbols) if ticker_symbols else 0
        }
        
    except Exception as e:
        logger.error(f"Error in update_market_data task: {e}")
        raise


# Periodic tasks configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    # Process news every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        process_news_articles.s(),
        name='process-news-every-5-minutes'
    )
    
    # Cleanup old articles daily at 2 AM
    sender.add_periodic_task(
        86400.0,  # 24 hours
        cleanup_old_articles.s(30),
        name='cleanup-old-articles-daily'
    )
    
    # Update market data every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour
        update_market_data.s(),
        name='update-market-data-hourly'
    )


if __name__ == '__main__':
    celery_app.start() 