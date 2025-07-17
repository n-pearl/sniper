from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from database import get_async_db
from services.news_service import news_service
from models.news_models import NewsArticle
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


# Pydantic models for request/response
class NewsArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    url: str
    source: str
    author: Optional[str] = None
    ticker_symbol: Optional[str] = None
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    published_at: str
    created_at: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    confidence_score: Optional[float] = None
    keywords: Optional[List[str]] = None
    entities: Optional[Dict[str, Any]] = None
    market_impact_score: Optional[float] = None
    is_processed: bool
    is_archived: bool
    
    # New enhanced sentiment fields
    sentiment_strength: Optional[float] = None
    sentiment_interpretation: Optional[str] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle UUID and datetime conversion"""
        
        # Generate sentiment interpretation if we have the data
        sentiment_interpretation = None
        if obj.sentiment_score is not None and obj.confidence_score is not None:
            strength = abs(obj.sentiment_score)
            if obj.sentiment_score > 0.15:
                direction = "Positive" if obj.sentiment_score < 0.4 else "Very Positive"
            elif obj.sentiment_score < -0.15:
                direction = "Negative" if obj.sentiment_score > -0.4 else "Very Negative"
            else:
                direction = "Neutral"
                
            confidence_desc = "High" if obj.confidence_score > 0.8 else "Moderate" if obj.confidence_score > 0.6 else "Low"
            sentiment_interpretation = f"{direction} ({confidence_desc} confidence)"
        
        data = {
            "id": str(obj.id),
            "title": obj.title,
            "content": obj.content,
            "summary": obj.summary,
            "url": obj.url,
            "source": obj.source,
            "author": obj.author,
            "ticker_symbol": obj.ticker_symbol,
            "company_name": obj.company_name,
            "sector": obj.sector,
            "industry": obj.industry,
            "published_at": obj.published_at.isoformat() if obj.published_at else None,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "sentiment_score": obj.sentiment_score,
            "sentiment_label": obj.sentiment_label,
            "confidence_score": obj.confidence_score,
            "keywords": obj.keywords,
            "entities": obj.entities,
            "market_impact_score": obj.market_impact_score,
            "is_processed": obj.is_processed,
            "is_archived": obj.is_archived,
            "sentiment_strength": abs(obj.sentiment_score) if obj.sentiment_score is not None else None,
            "sentiment_interpretation": sentiment_interpretation
        }
        return cls(**data)


class NewsFetchRequest(BaseModel):
    tickers: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    limit: Optional[int] = 50


class SentimentTrendsResponse(BaseModel):
    trends: List[Dict[str, Any]]
    summary: Dict[str, Any]


@router.get("/", response_model=List[NewsArticleResponse])
async def get_recent_news(
    hours: int = Query(24, description="Hours to look back"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    limit: int = Query(50, description="Maximum number of articles to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get recent news articles"""
    try:
        articles = await news_service.get_recent_articles(db, hours, ticker)
        return [NewsArticleResponse.from_orm(article) for article in articles[:limit]]
    except Exception as e:
        logger.error(f"Failed to get recent news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent news")


@router.post("/fetch", response_model=List[NewsArticleResponse])
async def fetch_news(
    request: NewsFetchRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Fetch and process news from Alpha Vantage"""
    try:
        articles = await news_service.fetch_and_process_news(
            db, 
            tickers=request.tickers, 
            topics=request.topics
        )
        return [NewsArticleResponse.from_orm(article) for article in articles]
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch and process news")


@router.get("/company/{symbol}", response_model=List[NewsArticleResponse])
async def get_company_news(
    symbol: str,
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Maximum number of articles to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get news for a specific company"""
    try:
        articles = await news_service.get_recent_articles(db, hours, symbol.upper())
        return [NewsArticleResponse.from_orm(article) for article in articles[:limit]]
    except Exception as e:
        logger.error(f"Failed to get company news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news for {symbol}")


@router.get("/sentiment/trends", response_model=SentimentTrendsResponse)
async def get_sentiment_trends(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    hours: int = Query(24, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get sentiment trends over time"""
    try:
        trends_data = await news_service.get_sentiment_trends(db, ticker, hours)
        return SentimentTrendsResponse(**trends_data)
    except Exception as e:
        logger.error(f"Failed to get sentiment trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment trends")


@router.get("/search/similar")
async def search_similar_articles(
    query: str = Query(..., description="Text to find similar articles for"),
    limit: int = Query(10, description="Maximum number of articles to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Search for articles similar to the given text"""
    try:
        # For now, we'll use a simple text search
        # In the future, this could use vector similarity
        query_filter = or_(
            NewsArticle.title.ilike(f"%{query}%"),
            NewsArticle.content.ilike(f"%{query}%")
        )
        
        db_query = select(NewsArticle).where(query_filter).order_by(NewsArticle.published_at.desc()).limit(limit)
        
        result = await db.execute(db_query)
        articles = result.scalars().all()
        
        return [NewsArticleResponse.from_orm(article) for article in articles]
    except Exception as e:
        logger.error(f"Failed to search similar articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to search articles")


@router.get("/stats")
async def get_news_stats(
    hours: int = Query(24, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get news statistics"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total articles
        total_query = select(func.count(NewsArticle.id)).where(
            NewsArticle.published_at >= cutoff_time
        )
        total_result = await db.execute(total_query)
        total_articles = total_result.scalar() or 0
        
        # Processed articles
        processed_query = select(func.count(NewsArticle.id)).where(
            and_(
                NewsArticle.published_at >= cutoff_time,
                NewsArticle.is_processed == True
            )
        )
        processed_result = await db.execute(processed_query)
        processed_articles = processed_result.scalar() or 0
        
        # Average sentiment
        sentiment_query = select(func.avg(NewsArticle.sentiment_score)).where(
            and_(
                NewsArticle.published_at >= cutoff_time,
                NewsArticle.sentiment_score.isnot(None)
            )
        )
        sentiment_result = await db.execute(sentiment_query)
        avg_sentiment = sentiment_result.scalar()
        
        # Top tickers
        ticker_query = select(
            NewsArticle.ticker_symbol,
            func.count(NewsArticle.id).label('count')
        ).where(
            and_(
                NewsArticle.published_at >= cutoff_time,
                NewsArticle.ticker_symbol.isnot(None)
            )
        ).group_by(NewsArticle.ticker_symbol).order_by(func.count(NewsArticle.id).desc()).limit(10)
        
        ticker_result = await db.execute(ticker_query)
        top_tickers = [{"ticker": row.ticker_symbol, "count": row.count} for row in ticker_result]
        
        return {
            "total_articles": total_articles,
            "processed_articles": processed_articles,
            "processing_rate": (processed_articles / total_articles * 100) if total_articles > 0 else 0,
            "average_sentiment": float(avg_sentiment) if avg_sentiment else 0.0,
            "top_tickers": top_tickers,
            "time_window_hours": hours
        }
    except Exception as e:
        logger.error(f"Failed to get news stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news statistics")


@router.post("/process/{article_id}")
async def reprocess_article(
    article_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Reprocess sentiment analysis for a specific article"""
    try:
        from uuid import UUID
        
        # Get article
        query = select(NewsArticle).where(NewsArticle.id == UUID(article_id))
        result = await db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Reprocess sentiment
        if hasattr(article, 'content') and article.content is not None:
            from sentiment.sentiment_engine import sentiment_engine
            sentiment_result = await sentiment_engine.analyze_ensemble(str(article.content))
            
            if sentiment_result:
                article.sentiment_score = sentiment_result["sentiment_score"]
                article.sentiment_label = sentiment_result["sentiment_label"]
                article.confidence_score = sentiment_result["confidence_score"]
                
                if "embedding_vector" in sentiment_result and sentiment_result["embedding_vector"]:
                    article.sentiment_vector = sentiment_result["embedding_vector"]
                
                # Use setattr to avoid type issues
                setattr(article, 'is_processed', True)
                await db.commit()
                await db.refresh(article)
                
                return {"message": "Article reprocessed successfully", "article": NewsArticleResponse.from_orm(article)}
        
        raise HTTPException(status_code=400, detail="Article has no content to process")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess article")


@router.post("/reprocess/binary", response_model=Dict[str, Any])
async def reprocess_binary_articles(
    batch_size: int = Query(default=50, description="Number of articles to reprocess"),
    model: str = Query(default="finbert", description="Model to use: finbert or ensemble"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reprocess articles with binary sentiment scores (-0.5, 0.5) using improved analysis
    Uses FinBERT-only by default to avoid OpenAI quota issues
    """
    try:
        # Find articles with binary sentiment scores
        query = select(NewsArticle).where(
            NewsArticle.sentiment_score.in_([-0.5, 0.5])
        ).limit(batch_size)
        
        result = await db.execute(query)
        articles = result.scalars().all()
        
        if not articles:
            return {
                "message": "No articles with binary scores found",
                "processed": 0,
                "errors": 0
            }
        
        processed_count = 0
        error_count = 0
        
        # Initialize sentiment engine
        from sentiment.sentiment_engine import sentiment_engine
        await sentiment_engine.initialize()
        
        for article in articles:
            try:
                # Get content for analysis
                content = article.content or article.title
                if not content or not content.strip():
                    logger.warning(f"No content for article {article.id}")
                    error_count += 1
                    continue
                
                # Choose analysis method based on parameter
                if model == "ensemble":
                    sentiment_result = await sentiment_engine.analyze_ensemble(content)
                else:
                    sentiment_result = await sentiment_engine.analyze_finbert(content)
                
                if sentiment_result:
                    # Update article with new sentiment data
                    article.sentiment_score = sentiment_result.get("sentiment_score")
                    article.sentiment_label = sentiment_result.get("sentiment_label")
                    article.confidence_score = sentiment_result.get("confidence_score")
                    
                    processed_count += 1
                    logger.info(f"Reprocessed article {article.id}: {article.sentiment_score:.4f}")
                else:
                    error_count += 1
                    logger.error(f"Failed to analyze sentiment for article {article.id}")
                
            except Exception as e:
                logger.error(f"Error processing article {article.id}: {e}")
                error_count += 1
                continue
        
        # Commit all changes
        await db.commit()
        
        return {
            "message": f"Batch reprocessing completed",
            "processed": processed_count,
            "errors": error_count,
            "model_used": model,
            "remaining_binary": len(articles) - processed_count if len(articles) > processed_count else 0
        }
        
    except Exception as e:
        logger.error(f"Error in batch reprocessing: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")


@router.post("/trigger-processing")
async def trigger_manual_processing(
    tickers: Optional[List[str]] = None,
    use_celery: bool = False
):
    """Manually trigger news processing (with optional Celery background processing)"""
    try:
        if use_celery:
            # Try using Celery if requested
            try:
                # Import here to avoid circular imports and handle Celery not being available
                import sys
                import importlib
                
                # Check if tasks module is available
                if 'tasks' not in sys.modules:
                    tasks_module = importlib.import_module('tasks')
                else:
                    tasks_module = sys.modules['tasks']
                
                # Get the task function and call delay
                process_task = getattr(tasks_module, 'process_news_articles', None)
                if process_task and hasattr(process_task, 'delay'):
                    task = process_task.delay(tickers)
                    return {
                        "message": "News processing triggered via Celery", 
                        "task_id": str(task.id),
                        "status": "queued"
                    }
                else:
                    raise ImportError("Celery task not available")
                    
            except Exception as e:
                logger.warning(f"Celery not available, falling back to direct processing: {e}")
                use_celery = False
        
        if not use_celery:
            # Direct processing without Celery
            from services.news_service import news_service
            from database import get_async_db
            
            # This is a workaround for dependency injection in manual calls
            async for db in get_async_db():
                articles = await news_service.fetch_and_process_news(db, tickers)
                return {
                    "message": "News processing completed", 
                    "articles_processed": len(articles),
                    "method": "direct"
                }
        
    except Exception as e:
        logger.error(f"Failed to trigger news processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger news processing")
