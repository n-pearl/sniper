import React, { useState, useEffect } from 'react';
import { Search, Filter, Calendar, TrendingUp, TrendingDown, Minus, ExternalLink } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function ArchiveLookup() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTicker, setSelectedTicker] = useState('');
  const [dateRange, setDateRange] = useState('7d');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (searchQuery || selectedTicker) {
      searchArticles();
    }
  }, [searchQuery, selectedTicker, dateRange, sentimentFilter, sortBy, currentPage]);

  const searchArticles = async () => {
    try {
      setLoading(true);
      
      // For now, we'll use the regular news endpoint with filters
      // In a real implementation, you'd have a dedicated search endpoint
      const response = await axios.get(`${API_BASE_URL}/news/search/similar`, {
        params: {
          query: searchQuery || 'financial news',
          limit: 20
        }
      });
      
      let filteredArticles = response.data;
      
      // Apply additional filters
      if (selectedTicker) {
        filteredArticles = filteredArticles.filter(article => 
          article.ticker_symbol?.toLowerCase().includes(selectedTicker.toLowerCase())
        );
      }
      
      if (sentimentFilter !== 'all') {
        filteredArticles = filteredArticles.filter(article => 
          article.sentiment_label === sentimentFilter
        );
      }
      
      // Sort articles
      filteredArticles.sort((a, b) => {
        switch (sortBy) {
          case 'date':
            return new Date(b.published_at) - new Date(a.published_at);
          case 'sentiment':
            return (b.sentiment_score || 0) - (a.sentiment_score || 0);
          case 'title':
            return a.title.localeCompare(b.title);
          default:
            return 0;
        }
      });
      
      setArticles(filteredArticles);
      setTotalPages(Math.ceil(filteredArticles.length / 10));
      setError(null);
    } catch (err) {
      console.error('Failed to search articles:', err);
      setError('Failed to search articles');
      // Use mock data for development
      setArticles(getMockArchiveData());
      setTotalPages(3);
    } finally {
      setLoading(false);
    }
  };

  const getMockArchiveData = () => [
    {
      id: '1',
      title: 'Apple Reports Record Q4 Revenue Driven by iPhone Sales',
      content: 'Apple Inc. announced record-breaking fourth-quarter revenue, with iPhone sales exceeding expectations and services revenue showing strong growth.',
      url: 'https://example.com/apple-q4-2023',
      source: 'Reuters',
      author: 'John Smith',
      ticker_symbol: 'AAPL',
      company_name: 'Apple Inc.',
      published_at: '2023-12-15T14:30:00Z',
      sentiment_score: 0.85,
      sentiment_label: 'positive',
      confidence_score: 0.94,
      is_processed: true
    },
    {
      id: '2',
      title: 'Tesla Faces Production Delays Due to Supply Chain Issues',
      content: 'Tesla has announced production delays for several models due to ongoing supply chain challenges affecting semiconductor availability.',
      url: 'https://example.com/tesla-delays-2023',
      source: 'Bloomberg',
      author: 'Jane Doe',
      ticker_symbol: 'TSLA',
      company_name: 'Tesla Inc.',
      published_at: '2023-12-14T09:15:00Z',
      sentiment_score: -0.45,
      sentiment_label: 'negative',
      confidence_score: 0.87,
      is_processed: true
    },
    {
      id: '3',
      title: 'Microsoft Cloud Services Show Strong Growth in Q3',
      content: 'Microsoft reported strong quarterly results with Azure cloud services leading the growth, exceeding analyst expectations.',
      url: 'https://example.com/microsoft-q3-2023',
      source: 'TechCrunch',
      author: 'Mike Johnson',
      ticker_symbol: 'MSFT',
      company_name: 'Microsoft Corporation',
      published_at: '2023-12-13T16:45:00Z',
      sentiment_score: 0.72,
      sentiment_label: 'positive',
      confidence_score: 0.91,
      is_processed: true
    },
    {
      id: '4',
      title: 'Google Announces New AI Research Initiative',
      content: 'Google has launched a new artificial intelligence research initiative focused on developing more advanced language models.',
      url: 'https://example.com/google-ai-2023',
      source: 'The Verge',
      author: 'Sarah Wilson',
      ticker_symbol: 'GOOGL',
      company_name: 'Alphabet Inc.',
      published_at: '2023-12-12T11:20:00Z',
      sentiment_score: 0.38,
      sentiment_label: 'positive',
      confidence_score: 0.83,
      is_processed: true
    },
    {
      id: '5',
      title: 'Amazon Faces Regulatory Scrutiny Over Market Dominance',
      content: 'Amazon is under increased regulatory scrutiny as lawmakers examine the company\'s market dominance in e-commerce.',
      url: 'https://example.com/amazon-regulation-2023',
      source: 'Wall Street Journal',
      author: 'David Brown',
      ticker_symbol: 'AMZN',
      company_name: 'Amazon.com Inc.',
      published_at: '2023-12-11T13:10:00Z',
      sentiment_score: -0.28,
      sentiment_label: 'negative',
      confidence_score: 0.79,
      is_processed: true
    }
  ];

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

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    searchArticles();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedTicker('');
    setDateRange('7d');
    setSentimentFilter('all');
    setSortBy('date');
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          News Archive & Search
        </h2>
        <p className="text-gray-600">
          Search and filter historical news articles with advanced sentiment analysis
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Bar */}
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search articles by title, content, or keywords..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ticker Symbol
              </label>
              <input
                type="text"
                placeholder="e.g., AAPL, TSLA"
                value={selectedTicker}
                onChange={(e) => setSelectedTicker(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date Range
              </label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="1d">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sentiment
              </label>
              <select
                value={sentimentFilter}
                onChange={(e) => setSentimentFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="date">Date (Newest)</option>
                <option value="sentiment">Sentiment Score</option>
                <option value="title">Title (A-Z)</option>
              </select>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={clearFilters}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Clear all filters
            </button>
            <div className="text-sm text-gray-500">
              {articles.length} articles found
            </div>
          </div>
        </form>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow">
        {error && (
          <div className="px-6 py-4 text-red-600 text-sm border-b border-gray-200">
            {error} - Showing mock data
          </div>
        )}

        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="border-b border-gray-200 pb-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        ) : articles.length === 0 ? (
          <div className="p-12 text-center">
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No articles found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search criteria or filters.
            </p>
          </div>
        ) : (
          <>
            {/* Articles List */}
            <div className="divide-y divide-gray-200">
              {articles.map((article) => (
                <ArchiveArticleCard
                  key={article.id}
                  article={article}
                  getSentimentIcon={getSentimentIcon}
                  getSentimentColor={getSentimentColor}
                  formatSentimentScore={formatSentimentScore}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function ArchiveArticleCard({ article, getSentimentIcon, getSentimentColor, formatSentimentScore }) {
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
            <h4 className="text-lg font-medium text-gray-900 line-clamp-2">
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

          <p className="mt-2 text-sm text-gray-600 line-clamp-3">
            {article.content}
          </p>

          {/* Meta Information */}
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span className="font-medium">{article.source}</span>
              {article.author && <span>by {article.author}</span>}
              <span className="flex items-center">
                <Calendar className="h-3 w-3 mr-1" />
                {format(new Date(article.published_at), 'MMM dd, yyyy')}
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

export default ArchiveLookup;
