import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from sentiment.sentiment_engine import SentimentEngine


@pytest.fixture
def sentiment_engine():
    return SentimentEngine()


@pytest.mark.asyncio
async def test_initialize_sentiment_engine(sentiment_engine):
    """Test sentiment engine initialization"""
    with patch('sentiment.sentiment_engine.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         patch('sentiment.sentiment_engine.AutoModelForSequenceClassification.from_pretrained') as mock_model, \
         patch('sentiment.sentiment_engine.openai.AsyncOpenAI') as mock_openai:
        
        mock_tokenizer.return_value = Mock()
        mock_model.return_value = Mock()
        mock_openai.return_value = Mock()
        
        await sentiment_engine.initialize()
        
        assert sentiment_engine._initialized is True
        assert sentiment_engine.finbert_tokenizer is not None
        assert sentiment_engine.finbert_model is not None


@pytest.mark.asyncio
async def test_preprocess_text(sentiment_engine):
    """Test text preprocessing"""
    # Test normal text
    text = "This is a test article about financial markets."
    processed = sentiment_engine._preprocess_text(text)
    assert processed == text
    
    # Test long text truncation
    long_text = "A" * 1000
    processed = sentiment_engine._preprocess_text(long_text)
    assert len(processed) <= 512
    
    # Test whitespace handling
    text_with_whitespace = "   Test text with spaces   "
    processed = sentiment_engine._preprocess_text(text_with_whitespace)
    assert processed == "Test text with spaces"


@pytest.mark.asyncio
async def test_analyze_finbert(sentiment_engine):
    """Test FinBERT sentiment analysis"""
    await sentiment_engine.initialize()
    
    with patch.object(sentiment_engine.finbert_tokenizer, '__call__') as mock_tokenizer, \
         patch.object(sentiment_engine.finbert_model, '__call__') as mock_model:
        
        # Mock tokenizer response
        mock_tokenizer.return_value = {'input_ids': Mock(), 'attention_mask': Mock()}
        
        # Mock model response
        mock_outputs = Mock()
        mock_outputs.logits = Mock()
        mock_outputs.logits.item.return_value = 2  # Positive sentiment
        mock_model.return_value = mock_outputs
        
        result = await sentiment_engine.analyze_finbert("Apple reports strong earnings")
        
        assert result['sentiment_label'] == 'positive'
        assert result['sentiment_score'] == 0.5
        assert result['model_name'] == 'finbert'
        assert 'processing_time_ms' in result


@pytest.mark.asyncio
async def test_analyze_openai(sentiment_engine):
    """Test OpenAI sentiment analysis"""
    await sentiment_engine.initialize()
    
    with patch.object(sentiment_engine.openai_client.chat.completions, 'create') as mock_create:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"sentiment_score": 0.8, "sentiment_label": "positive", "confidence_score": 0.9}'
        mock_create.return_value = mock_response
        
        result = await sentiment_engine.analyze_openai("Positive financial news")
        
        assert result['sentiment_score'] == 0.8
        assert result['sentiment_label'] == 'positive'
        assert result['confidence_score'] == 0.9
        assert result['model_name'] == 'openai'


@pytest.mark.asyncio
async def test_analyze_ensemble(sentiment_engine):
    """Test ensemble sentiment analysis"""
    await sentiment_engine.initialize()
    
    with patch.object(sentiment_engine, 'analyze_finbert') as mock_finbert, \
         patch.object(sentiment_engine, 'analyze_openai') as mock_openai:
        
        mock_finbert.return_value = {
            'sentiment_score': 0.5,
            'sentiment_label': 'positive',
            'confidence_score': 0.8
        }
        
        mock_openai.return_value = {
            'sentiment_score': 0.7,
            'sentiment_label': 'positive',
            'confidence_score': 0.9
        }
        
        result = await sentiment_engine.analyze_ensemble("Test article")
        
        # Weighted average: 0.5 * 0.6 + 0.7 * 0.4 = 0.58
        expected_score = 0.5 * 0.6 + 0.7 * 0.4
        assert abs(result['sentiment_score'] - expected_score) < 0.01
        assert result['sentiment_label'] == 'positive'
        assert result['model_name'] == 'ensemble'


@pytest.mark.asyncio
async def test_analyze_batch(sentiment_engine):
    """Test batch sentiment analysis"""
    await sentiment_engine.initialize()
    
    texts = ["Positive news", "Negative news", "Neutral news"]
    
    with patch.object(sentiment_engine, 'analyze_ensemble') as mock_ensemble:
        mock_ensemble.return_value = {
            'sentiment_score': 0.5,
            'sentiment_label': 'positive',
            'confidence_score': 0.8
        }
        
        results = await sentiment_engine.analyze_batch(texts)
        
        assert len(results) == 3
        assert all(result['model_name'] == 'ensemble' for result in results)


@pytest.mark.asyncio
async def test_analyze_finbert_error_handling(sentiment_engine):
    """Test FinBERT error handling"""
    await sentiment_engine.initialize()
    
    with patch.object(sentiment_engine.finbert_tokenizer, '__call__', side_effect=Exception("Tokenization error")):
        result = await sentiment_engine.analyze_finbert("Test text")
        
        assert result['sentiment_score'] == 0.0
        assert result['sentiment_label'] == 'neutral'
        assert 'error' in result


@pytest.mark.asyncio
async def test_analyze_openai_no_client(sentiment_engine):
    """Test OpenAI analysis when client is not initialized"""
    sentiment_engine.openai_client = None
    
    result = await sentiment_engine.analyze_openai("Test text")
    
    assert result is None


if __name__ == "__main__":
    pytest.main([__file__]) 