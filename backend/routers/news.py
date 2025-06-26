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
    
    class Config:
        from_attributes = True


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
