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

    // Keyboard shortcuts
    const handleClearFilters = () => {
      setFilter('all');
      setTickerFilter('');
    };

    window.addEventListener('clearFilters', handleClearFilters);

    return () => {
      clearInterval(interval);
      window.removeEventListener('clearFilters', handleClearFilters);
    };
  }, [autoRefresh]);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/news/`, {
        params: {
          hours: 24,
          limit: 50
        }
      });
      setArticles(response.data);
    } catch (err) {
      console.error('Failed to fetch articles:', err);
      setError('Failed to load news articles - using sample data');
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
      case 'strongly_positive':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'negative':
      case 'strongly_negative':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive':
      case 'strongly_positive':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'negative':
      case 'strongly_negative':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatSentimentScore = (score) => {
    if (score === null || score === undefined) return 'N/A';
    // Score is already in range -1 to 1, so multiply by 100 for percentage
    return (score * 100).toFixed(0);
  };

  const refreshArticles = async () => {
    await fetchArticles();
  };

  const getTimeAgo = (dateString) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (error) {
      return 'Unknown time';
    }
  };

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 border border-gray-200 dark:border-dark-700 transition-all duration-300">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Real-Time News Feed</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Latest financial news with sentiment analysis ({filteredArticles.length} articles)
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={refreshArticles}
              disabled={loading}
              className="px-3 py-1 text-sm bg-blue-600 dark:bg-blue-500 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
            <label className="flex items-center text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2 rounded border-gray-300 dark:border-dark-600 text-blue-600 focus:ring-blue-500 dark:bg-dark-700"
              />
              Auto-refresh
            </label>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Sentiment:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="text-sm border border-gray-300 dark:border-dark-600 rounded px-2 py-1 bg-white dark:bg-dark-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            >
              <option value="all">All</option>
              <option value="positive">Positive</option>
              <option value="strongly_positive">Strongly Positive</option>
              <option value="negative">Negative</option>
              <option value="strongly_negative">Strongly Negative</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Ticker:</span>
            <input
              type="text"
              placeholder="Filter by ticker..."
              value={tickerFilter}
              onChange={(e) => setTickerFilter(e.target.value)}
              className="text-sm border border-gray-300 dark:border-dark-600 rounded px-2 py-1 w-32 bg-white dark:bg-dark-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            />
          </div>
        </div>
      </div>

      {/* Articles List */}
      <div className="divide-y divide-gray-200 dark:divide-dark-700 max-h-[600px] overflow-y-auto">
        {error && (
          <div className="px-6 py-4 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-500">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-yellow-700 dark:text-yellow-400">{error}</p>
              </div>
            </div>
          </div>
        )}
        
        {loading && (
          <div className="px-6 py-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading articles...</p>
          </div>
        )}
        
        {!loading && filteredArticles.length === 0 && (
          <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
            <p>No articles found matching your filters.</p>
            <button 
              onClick={() => { setFilter('all'); setTickerFilter(''); }}
              className="mt-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
            >
              Clear filters
            </button>
          </div>
        )}
        
        {!loading && filteredArticles.map((article) => (
          <ArticleCard 
            key={article.id} 
            article={article} 
            getSentimentIcon={getSentimentIcon}
            getSentimentColor={getSentimentColor}
            formatSentimentScore={formatSentimentScore}
            getTimeAgo={getTimeAgo}
          />
        ))}
      </div>
    </div>
  );
}

function ArticleCard({ article, getSentimentIcon, getSentimentColor, formatSentimentScore, getTimeAgo }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSentimentColorDark = (sentiment) => {
    switch (sentiment) {
      case 'positive':
      case 'strongly_positive':
        return 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800';
      case 'negative':
      case 'strongly_negative':
        return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600';
    }
  };

  return (
    <div className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-dark-700/50 transition-colors duration-200">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getSentimentColorDark(article.sentiment_label)}`}>
              {getSentimentIcon(article.sentiment_label)}
              <span className="ml-1">{formatSentimentScore(article.sentiment_score)}%</span>
            </span>
            {article.ticker_symbol && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                {article.ticker_symbol}
              </span>
            )}
            <span className="text-xs text-gray-500 dark:text-gray-400">{article.source}</span>
          </div>
          
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1 line-clamp-2">
            {article.title}
          </h4>
          
          <p className={`text-sm text-gray-600 dark:text-gray-300 ${isExpanded ? '' : 'line-clamp-2'}`}>
            {article.content}
          </p>
          
          {article.content && article.content.length > 150 && (
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 mt-1 transition-colors"
            >
              {isExpanded ? 'Show less' : 'Show more'}
            </button>
          )}
          
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                {getTimeAgo(article.published_at)}
              </span>
              {article.author && (
                <span>By {article.author}</span>
              )}
            </div>
            
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Read more
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NewsFeed;
