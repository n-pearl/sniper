import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from config import settings
from models.news_models import NewsArticle
from sentiment.sentiment_engine import sentiment_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def fetch_news_sentiment(self, tickers: Optional[List[str]] = None, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch news sentiment from Alpha Vantage"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            return []
        
        try:
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": self.api_key,
                "limit": settings.MAX_ARTICLES_PER_REQUEST
            }
            
            if tickers:
                params["tickers"] = ",".join(tickers)
            if topics:
                params["topics"] = ",".join(topics)
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "feed" not in data:
                logger.warning("No news feed found in response")
                return []
            
            return data["feed"]
            
        except Exception as e:
            logger.error(f"Failed to fetch news sentiment: {e}")
            return []
    
    async def fetch_company_news(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch company-specific news"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            return []
        
        try:
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.api_key,
                "limit": limit
            }
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "feed" not in data:
                logger.warning(f"No news found for symbol {symbol}")
                return []
            
            return data["feed"]
            
        except Exception as e:
            logger.error(f"Failed to fetch company news for {symbol}: {e}")
            return []
    
    def _parse_news_article(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Alpha Vantage news article data"""
        try:
            # Extract basic article info
            article = {
                "title": article_data.get("title", ""),
                "content": article_data.get("summary", ""),
                "url": article_data.get("url", ""),
                "source": article_data.get("source", ""),
                "author": article_data.get("authors", ""),
                "published_at": datetime.fromisoformat(article_data.get("time_published", "").replace("Z", "+00:00")),
                "raw_data": article_data
            }
            
            # Extract ticker information
            ticker_data = article_data.get("ticker_sentiment", [])
            if ticker_data:
                # Use the first ticker for now (could be enhanced to handle multiple)
                ticker_info = ticker_data[0]
                article["ticker_symbol"] = ticker_info.get("ticker", "")
                article["company_name"] = ticker_info.get("ticker_name", "")
                
                # Extract Alpha Vantage sentiment (if available)
                av_sentiment = ticker_info.get("ticker_sentiment_score", 0)
                article["alpha_vantage_sentiment"] = float(av_sentiment) if av_sentiment else None
            
            # Extract topics and categories
            topics = article_data.get("topics", [])
            if topics:
                article["keywords"] = [topic.get("topic", "") for topic in topics]
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to parse news article: {e}")
            return None
    
    async def process_and_store_articles(self, db: AsyncSession, articles_data: List[Dict[str, Any]]) -> List[NewsArticle]:
        """Process articles and store them in the database"""
        processed_articles = []
        
        for article_data in articles_data:
            try:
                # Parse article data
                parsed_article = self._parse_news_article(article_data)
                if not parsed_article:
                    continue
                
                # Check if article already exists
                existing = await db.execute(
                    select(NewsArticle).where(NewsArticle.url == parsed_article["url"])
                )
                if existing.scalar_one_or_none():
                    logger.debug(f"Article already exists: {parsed_article['title'][:50]}...")
                    continue
                
                # Create new article
                article = NewsArticle(**parsed_article)
                
                # Perform sentiment analysis
                if article.content is not None:
                    sentiment_result = await sentiment_engine.analyze_ensemble(str(article.content))
                    
                    if sentiment_result:
                        article.sentiment_score = sentiment_result["sentiment_score"]
                        article.sentiment_label = sentiment_result["sentiment_label"]
                        article.confidence_score = sentiment_result["confidence_score"]
                        
                        # Store embedding if available
                        if "embedding_vector" in sentiment_result and sentiment_result["embedding_vector"]:
                            article.sentiment_vector = sentiment_result["embedding_vector"]
                        
                        setattr(article, 'is_processed', True)
                
                # Add to database
                db.add(article)
                await db.commit()
                await db.refresh(article)
                
                processed_articles.append(article)
                logger.info(f"Processed and stored article: {article.title[:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                await db.rollback()
                continue
        
        return processed_articles
    
    async def fetch_and_process_news(self, db: AsyncSession, tickers: Optional[List[str]] = None, topics: Optional[List[str]] = None) -> List[NewsArticle]:
        """Fetch news from Alpha Vantage and process it"""
        # Fetch news data
        articles_data = await self.fetch_news_sentiment(tickers, topics)
        
        if not articles_data:
            logger.warning("No articles fetched from Alpha Vantage")
            return []
        
        # Process and store articles
        processed_articles = await self.process_and_store_articles(db, articles_data)
        
        logger.info(f"Successfully processed {len(processed_articles)} articles")
        return processed_articles
    
    async def get_recent_articles(self, db: AsyncSession, hours: int = 24, ticker: Optional[str] = None) -> List[NewsArticle]:
        """Get recent articles from the database"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(NewsArticle).where(
                and_(
                    NewsArticle.published_at >= cutoff_time,
                    NewsArticle.is_processed == True
                )
            ).order_by(NewsArticle.published_at.desc())
            
            if ticker:
                query = query.where(NewsArticle.ticker_symbol == ticker)
            
            result = await db.execute(query)
            articles = result.scalars().all()
            
            return list(articles)
            
        except Exception as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []
    
    async def search_similar_articles(self, db: AsyncSession, query_vector: List[float], limit: int = 10) -> List[NewsArticle]:
        """Search for articles similar to the given vector"""
        try:
            # Use pgvector cosine similarity
            query = select(NewsArticle).where(
                NewsArticle.sentiment_vector.isnot(None)
            ).order_by(
                NewsArticle.sentiment_vector.cosine_distance(query_vector)
            ).limit(limit)
            
            result = await db.execute(query)
            articles = result.scalars().all()
            
            return list(articles)
            
        except Exception as e:
            logger.error(f"Failed to search similar articles: {e}")
            return []
    
    async def get_sentiment_trends(self, db: AsyncSession, ticker: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get sentiment trends over time"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(NewsArticle).where(
                and_(
                    NewsArticle.published_at >= cutoff_time,
                    NewsArticle.sentiment_score.isnot(None),
                    NewsArticle.is_processed == True
                )
            )
            
            if ticker:
                query = query.where(NewsArticle.ticker_symbol == ticker)
            
            result = await db.execute(query)
            articles = result.scalars().all()
            
            if not articles:
                return {"trends": [], "summary": {}}
            
            # Calculate trends
            sentiment_scores = [article.sentiment_score for article in articles]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            # Count sentiment labels
            sentiment_counts = {}
            for article in articles:
                label = article.sentiment_label
                sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
            
            return {
                "trends": [
                    {
                        "published_at": article.published_at.isoformat(),
                        "sentiment_score": article.sentiment_score,
                        "title": article.title,
                        "ticker": article.ticker_symbol
                    }
                    for article in articles
                ],
                "summary": {
                    "total_articles": len(articles),
                    "average_sentiment": avg_sentiment,
                    "sentiment_distribution": sentiment_counts
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get sentiment trends: {e}")
            return {"trends": [], "summary": {}}


# Global news service instance
news_service = NewsService()
