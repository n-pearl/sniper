from celery import Celery
from config import settings
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app with better configuration
celery_app = Celery(
    "sniper",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks']
)

# Better Celery configuration to prevent loops
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=5 * 60,  # 5 minutes max
    task_soft_time_limit=4 * 60,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,  # Restart workers after 100 tasks
    task_acks_late=True,
    worker_disable_rate_limits=True,
    task_reject_on_worker_lost=True,
)


@celery_app.task(bind=True, name="fetch_single_batch")
def fetch_single_batch(self, ticker_symbols: Optional[List[str]] = None, max_articles: int = 20):
    """
    Fetch a single batch of articles - prevents infinite loops
    """
    try:
        logger.info(f"Fetching single batch for tickers: {ticker_symbols}")
        
        if not settings.ALPHA_VANTAGE_API_KEY:
            logger.error("Alpha Vantage API key not configured")
            return {"status": "error", "message": "API key not configured"}
        
        # Fetch from Alpha Vantage with strict limits
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
            "limit": min(max_articles, 50)  # Never more than 50
        }
        
        if ticker_symbols:
            params["tickers"] = ",".join(ticker_symbols[:3])  # Max 3 tickers
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get("https://www.alphavantage.co/query", params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("feed", [])
            
            if not articles:
                return {"status": "completed", "articles_fetched": 0, "new_articles": 0}
            
            # Process articles one by one to avoid overwhelming the system
            new_count = 0
            for article in articles[:max_articles]:  # Strict limit
                try:
                    # Queue individual processing
                    process_single_article.delay(article)
                    new_count += 1
                except Exception as e:
                    logger.error(f"Error queuing article: {e}")
                    continue
            
            return {
                "status": "completed", 
                "articles_fetched": len(articles),
                "articles_queued": new_count
            }
            
    except Exception as e:
        logger.error(f"Error in fetch_single_batch: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="process_single_article", max_retries=2)
def process_single_article(self, article_data: Dict[str, Any]):
    """
    Process a single article with proper duplicate checking
    """
    try:
        article_url = article_data.get('url', '')
        if not article_url:
            return {"status": "skipped", "reason": "no_url"}
        
        # Import here to avoid circular imports
        from database import SessionLocal
        from models.news_models import NewsArticle
        from sentiment.sentiment_engine import sentiment_engine
        
        db = SessionLocal()
        try:
            # Check if article already exists
            existing = db.query(NewsArticle).filter(NewsArticle.url == article_url).first()
            if existing:
                if existing.is_processed:
                    return {"status": "skipped", "reason": "already_processed"}
                else:
                    # Update existing unprocessed article
                    article = existing
            else:
                # Create new article
                article = NewsArticle(
                    title=article_data.get('title', ''),
                    content=article_data.get('summary', ''),
                    url=article_url,
                    source=article_data.get('source', ''),
                    author=', '.join(article_data.get('authors', [])) if article_data.get('authors') else '',
                    published_at=datetime.fromisoformat(article_data.get('time_published', '').replace("Z", "+00:00")) if article_data.get('time_published') else datetime.utcnow(),
                    raw_data=article_data
                )
                
                # Extract ticker if available
                if article_data.get('ticker_sentiment'):
                    ticker_info = article_data['ticker_sentiment'][0]
                    article.ticker_symbol = ticker_info.get('ticker', '')
                
                db.add(article)
                db.flush()  # Get ID
            
            # Process sentiment if content available
            content = article.content or article.title
            if content.strip():
                # Initialize sentiment engine if not already done
                asyncio.run(sentiment_engine.initialize())
                
                # Analyze sentiment using the improved method
                sentiment_result = asyncio.run(sentiment_engine.analyze_ensemble(content))
                
                if sentiment_result:
                    article.sentiment_score = sentiment_result.get("sentiment_score")
                    article.sentiment_label = sentiment_result.get("sentiment_label")
                    article.confidence_score = sentiment_result.get("confidence_score")
                    article.is_processed = True
            
            db.commit()
            logger.info(f"Successfully processed: {article.title[:50]}...")
            
            return {
                "status": "completed",
                "article_id": str(article.id),
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing article: {e}")
        # Retry mechanism
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=e)
        return {"status": "error", "message": str(e)}


@celery_app.task(name="cleanup_old_articles")
def cleanup_old_articles(days_old: int = 30):
    """
    Simple cleanup task
    """
    try:
        from database import SessionLocal
        from models.news_models import NewsArticle
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        db = SessionLocal()
        
        try:
            # Just mark as archived, don't delete
            old_articles = db.query(NewsArticle).filter(
                NewsArticle.published_at < cutoff_date,
                NewsArticle.is_archived == False
            ).limit(100)  # Process in batches
            
            count = 0
            for article in old_articles:
                article.is_archived = True
                count += 1
            
            db.commit()
            return {"status": "completed", "archived_count": count}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {"status": "error", "message": str(e)}


# CONTROLLED periodic tasks - much less frequent
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks with safe intervals"""
    
    # Fetch news every 30 minutes (not 5!)
    sender.add_periodic_task(
        1800.0,  # 30 minutes
        fetch_single_batch.s(max_articles=10),  # Only 10 articles per batch
        name='fetch-news-every-30-minutes'
    )
    
    # Cleanup once daily
    sender.add_periodic_task(
        86400.0,  # 24 hours  
        cleanup_old_articles.s(30),
        name='cleanup-daily'
    )
    
    logger.info("Celery periodic tasks configured with safe intervals")


if __name__ == '__main__':
    celery_app.start() 