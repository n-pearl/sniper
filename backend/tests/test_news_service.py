import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from services.news_service import NewsService
from models.news_models import NewsArticle


@pytest.fixture
def news_service():
    return NewsService()


@pytest.fixture
def mock_article_data():
    return {
        "title": "Test Article",
        "summary": "This is a test article about financial markets.",
        "url": "https://example.com/test",
        "source": "Test Source",
        "authors": "Test Author",
        "time_published": "2024-01-01T10:00:00Z",
        "ticker_sentiment": [
            {
                "ticker": "AAPL",
                "ticker_name": "Apple Inc.",
                "ticker_sentiment_score": "0.8"
            }
        ],
        "topics": [
            {"topic": "technology"},
            {"topic": "earnings"}
        ]
    }


@pytest.mark.asyncio
async def test_fetch_news_sentiment_success(news_service):
    """Test successful news sentiment fetching"""
    with patch.object(news_service.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"feed": [{"title": "Test"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = await news_service.fetch_news_sentiment(tickers=["AAPL"])
        
        assert len(result) == 1
        assert result[0]["title"] == "Test"


@pytest.mark.asyncio
async def test_fetch_news_sentiment_no_api_key(news_service):
    """Test news fetching without API key"""
    news_service.api_key = ""
    
    result = await news_service.fetch_news_sentiment()
    
    assert result == []


@pytest.mark.asyncio
async def test_fetch_news_sentiment_error(news_service):
    """Test news fetching with error"""
    with patch.object(news_service.client, 'get', side_effect=Exception("API Error")):
        result = await news_service.fetch_news_sentiment()
        
        assert result == []


@pytest.mark.asyncio
async def test_parse_news_article(news_service, mock_article_data):
    """Test news article parsing"""
    result = news_service._parse_news_article(mock_article_data)
    
    assert result["title"] == "Test Article"
    assert result["content"] == "This is a test article about financial markets."
    assert result["url"] == "https://example.com/test"
    assert result["source"] == "Test Source"
    assert result["author"] == "Test Author"
    assert result["ticker_symbol"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["alpha_vantage_sentiment"] == 0.8
    assert "technology" in result["keywords"]
    assert "earnings" in result["keywords"]


@pytest.mark.asyncio
async def test_parse_news_article_error(news_service):
    """Test news article parsing with error"""
    invalid_data = {"invalid": "data"}
    
    result = news_service._parse_news_article(invalid_data)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_recent_articles(news_service):
    """Test getting recent articles from database"""
    mock_db = AsyncMock()
    mock_articles = [
        Mock(
            id="1",
            title="Test Article",
            content="Test content",
            url="https://example.com",
            source="Test Source",
            published_at=datetime.utcnow(),
            ticker_symbol="AAPL",
            sentiment_score=0.5,
            sentiment_label="positive",
            is_processed=True
        )
    ]
    
    with patch('services.news_service.select') as mock_select, \
         patch('services.news_service.and_') as mock_and:
        
        mock_query = Mock()
        mock_select.return_value = mock_query
        mock_and.return_value = Mock()
        
        mock_db.execute.return_value = Mock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_articles
        
        result = await news_service.get_recent_articles(mock_db, hours=24, ticker="AAPL")
        
        assert len(result) == 1
        assert result[0].title == "Test Article"


@pytest.mark.asyncio
async def test_get_sentiment_trends(news_service):
    """Test getting sentiment trends"""
    mock_db = AsyncMock()
    mock_articles = [
        Mock(
            published_at=datetime.utcnow(),
            sentiment_score=0.5,
            sentiment_label="positive",
            title="Test Article",
            ticker_symbol="AAPL"
        ),
        Mock(
            published_at=datetime.utcnow(),
            sentiment_score=-0.3,
            sentiment_label="negative",
            title="Test Article 2",
            ticker_symbol="TSLA"
        )
    ]
    
    with patch('services.news_service.select') as mock_select, \
         patch('services.news_service.and_') as mock_and:
        
        mock_query = Mock()
        mock_select.return_value = mock_query
        mock_and.return_value = Mock()
        
        mock_db.execute.return_value = Mock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_articles
        
        result = await news_service.get_sentiment_trends(mock_db, ticker="AAPL", hours=24)
        
        assert "trends" in result
        assert "summary" in result
        assert result["summary"]["total_articles"] == 2
        assert result["summary"]["average_sentiment"] == 0.1  # (0.5 + (-0.3)) / 2


@pytest.mark.asyncio
async def test_search_similar_articles(news_service):
    """Test searching similar articles"""
    mock_db = AsyncMock()
    query_vector = [0.1, 0.2, 0.3] * 256  # 768-dimensional vector
    
    mock_articles = [
        Mock(
            id="1",
            title="Similar Article",
            content="Similar content",
            url="https://example.com",
            source="Test Source",
            published_at=datetime.utcnow(),
            ticker_symbol="AAPL",
            sentiment_score=0.5,
            sentiment_label="positive",
            is_processed=True
        )
    ]
    
    with patch('services.news_service.select') as mock_select:
        mock_query = Mock()
        mock_select.return_value = mock_query
        
        mock_db.execute.return_value = Mock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_articles
        
        result = await news_service.search_similar_articles(mock_db, query_vector, limit=10)
        
        assert len(result) == 1
        assert result[0].title == "Similar Article"


@pytest.mark.asyncio
async def test_fetch_and_process_news(news_service):
    """Test fetching and processing news"""
    mock_db = AsyncMock()
    mock_articles_data = [{"title": "Test Article", "summary": "Test content"}]
    
    with patch.object(news_service, 'fetch_news_sentiment', return_value=mock_articles_data), \
         patch.object(news_service, 'process_and_store_articles', return_value=[]):
        
        result = await news_service.fetch_and_process_news(mock_db, tickers=["AAPL"])
        
        assert result == []


@pytest.mark.asyncio
async def test_fetch_and_process_news_no_data(news_service):
    """Test fetching and processing news with no data"""
    mock_db = AsyncMock()
    
    with patch.object(news_service, 'fetch_news_sentiment', return_value=[]):
        result = await news_service.fetch_and_process_news(mock_db)
        
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__]) 