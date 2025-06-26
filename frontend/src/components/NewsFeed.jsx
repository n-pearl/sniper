import React, { useState, useEffect } from 'react';
import { ExternalLink, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function NewsFeed() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, positive, negative, neutral
  const [tickerFilter, setTickerFilter] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchArticles();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchArticles();
      }
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/news/`, {
        params: {
          hours: 24,
          limit: 50
        }
      });
      setArticles(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch articles:', err);
      setError('Failed to load news articles');
      // Use mock data for development
      setArticles(getMockArticles());
    } finally {
      setLoading(false);
    }
  };

  const getMockArticles = () => [
    {
      id: '1',
      title: 'Apple Reports Strong Q4 Earnings, Exceeds Expectations',
      content: 'Apple Inc. reported quarterly earnings that exceeded analyst expectations, driven by strong iPhone sales and services revenue growth.',
      url: 'https://example.com/apple-earnings',
      source: 'Reuters',
      author: 'John Smith',
      ticker_symbol: 'AAPL',
      company_name: 'Apple Inc.',
      published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      sentiment_score: 0.8,
      sentiment_label: 'positive',
      confidence_score: 0.92,
      is_processed: true
    },
    {
      id: '2',
      title: 'Tesla Faces Regulatory Scrutiny Over Safety Concerns',
      content: 'Tesla is under investigation by federal regulators following reports of safety issues with its autonomous driving features.',
      url: 'https://example.com/tesla-safety',
      source: 'Bloomberg',
      author: 'Jane Doe',
      ticker_symbol: 'TSLA',
      company_name: 'Tesla Inc.',
      published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      sentiment_score: -0.6,
      sentiment_label: 'negative',
      confidence_score: 0.88,
      is_processed: true
    },
    {
      id: '3',
      title: 'Microsoft Announces New AI Partnership',
      content: 'Microsoft has announced a strategic partnership with OpenAI to advance artificial intelligence research and development.',
      url: 'https://example.com/microsoft-ai',
      source: 'TechCrunch',
      author: 'Mike Johnson',
      ticker_symbol: 'MSFT',
      company_name: 'Microsoft Corporation',
      published_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      sentiment_score: 0.3,
      sentiment_label: 'positive',
      confidence_score: 0.85,
      is_processed: true
    }
  ];

  const filteredArticles = articles.filter(article => {
    const matchesFilter = filter === 'all' || article.sentiment_label === filter;
    const matchesTicker = !tickerFilter || 
      (article.ticker_symbol && article.ticker_symbol.toLowerCase().includes(tickerFilter.toLowerCase()));
    return matchesFilter && matchesTicker;
  });

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'negative':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'negative':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatSentimentScore = (score) => {
    if (score === null || score === undefined) return 'N/A';
    return (score * 100).toFixed(0);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Real-Time News Feed</h3>
            <p className="text-sm text-gray-500">
              Latest financial news with sentiment analysis
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={fetchArticles}
              disabled={loading}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              Auto-refresh
            </label>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Sentiment:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="all">All</option>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Ticker:</span>
            <input
              type="text"
              placeholder="Filter by ticker..."
              value={tickerFilter}
              onChange={(e) => setTickerFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1 w-24"
            />
          </div>
        </div>
      </div>

      {/* Articles List */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {error && (
          <div className="px-6 py-4 text-red-600 text-sm">
            {error} - Showing mock data
          </div>
        )}
        
        {filteredArticles.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            {loading ? 'Loading articles...' : 'No articles found'}
          </div>
        ) : (
          filteredArticles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              getSentimentIcon={getSentimentIcon}
              getSentimentColor={getSentimentColor}
              formatSentimentScore={formatSentimentScore}
            />
          ))
        )}
      </div>
    </div>
  );
}

function ArticleCard({ article, getSentimentIcon, getSentimentColor, formatSentimentScore }) {
  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start space-x-4">
        {/* Sentiment Indicator */}
        <div className="flex-shrink-0 mt-1">
          {getSentimentIcon(article.sentiment_label)}
        </div>

        {/* Article Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
              {article.title}
            </h4>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          <p className="mt-1 text-sm text-gray-600 line-clamp-2">
            {article.content}
          </p>

          {/* Meta Information */}
          <div className="mt-2 flex items-center justify-between">
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span>{article.source}</span>
              {article.author && <span>by {article.author}</span>}
              <span className="flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                {formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              {article.ticker_symbol && (
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                  {article.ticker_symbol}
                </span>
              )}
              <span className={`px-2 py-1 text-xs font-medium border rounded ${getSentimentColor(article.sentiment_label)}`}>
                {formatSentimentScore(article.sentiment_score)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NewsFeed;
