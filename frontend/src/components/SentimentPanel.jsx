import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Target } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function SentimentPanel() {
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTicker, setSelectedTicker] = useState('');
  const [timeRange, setTimeRange] = useState(24);

  useEffect(() => {
    fetchSentimentTrends();
  }, [selectedTicker, timeRange]);

  const fetchSentimentTrends = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/news/sentiment/trends`, {
        params: {
          ticker: selectedTicker || undefined,
          hours: timeRange
        }
      });
      setTrendsData(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sentiment trends:', err);
      setError('Failed to load sentiment trends');
      // Use mock data for development
      setTrendsData(getMockTrendsData());
    } finally {
      setLoading(false);
    }
  };

  const getMockTrendsData = () => ({
    trends: [
      { published_at: '2024-01-01T10:00:00Z', sentiment_score: 0.8, title: 'Apple Earnings Beat', ticker: 'AAPL' },
      { published_at: '2024-01-01T11:00:00Z', sentiment_score: -0.6, title: 'Tesla Safety Issues', ticker: 'TSLA' },
      { published_at: '2024-01-01T12:00:00Z', sentiment_score: 0.3, title: 'Microsoft AI Partnership', ticker: 'MSFT' },
      { published_at: '2024-01-01T13:00:00Z', sentiment_score: 0.9, title: 'Google Cloud Growth', ticker: 'GOOGL' },
      { published_at: '2024-01-01T14:00:00Z', sentiment_score: -0.2, title: 'Amazon Competition', ticker: 'AMZN' },
      { published_at: '2024-01-01T15:00:00Z', sentiment_score: 0.5, title: 'Meta VR Success', ticker: 'META' },
    ],
    summary: {
      total_articles: 6,
      average_sentiment: 0.28,
      sentiment_distribution: {
        positive: 4,
        negative: 1,
        neutral: 1
      }
    }
  });

  const formatChartData = (trends) => {
    return trends.map((item, index) => ({
      time: index + 1,
      sentiment: item.sentiment_score * 100,
      title: item.title,
      ticker: item.ticker
    }));
  };

  const formatPieData = (distribution) => {
    return Object.entries(distribution).map(([label, value]) => ({
      name: label.charAt(0).toUpperCase() + label.slice(1),
      value,
      color: label === 'positive' ? '#10B981' : label === 'negative' ? '#EF4444' : '#6B7280'
    }));
  };

  const getSentimentTrend = (average) => {
    if (average > 0.1) return { direction: 'up', color: 'text-green-600', icon: TrendingUp };
    if (average < -0.1) return { direction: 'down', color: 'text-red-600', icon: TrendingDown };
    return { direction: 'neutral', color: 'text-gray-600', icon: Activity };
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const trend = getSentimentTrend(trendsData?.summary?.average_sentiment || 0);
  const TrendIcon = trend.icon;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Sentiment Analysis</h3>
            <p className="text-sm text-gray-500">
              Real-time sentiment trends and distribution
            </p>
          </div>
          <TrendIcon className={`h-5 w-5 ${trend.color}`} />
        </div>

        {/* Controls */}
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Ticker:</span>
            <input
              type="text"
              placeholder="All tickers"
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1 w-20"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Time:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value={1}>1 hour</option>
              <option value={6}>6 hours</option>
              <option value={24}>24 hours</option>
              <option value={168}>7 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {error && (
          <div className="text-red-600 text-sm">
            {error} - Showing mock data
          </div>
        )}

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {trendsData?.summary?.total_articles || 0}
            </div>
            <div className="text-sm text-gray-500">Total Articles</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className={`text-2xl font-bold ${trend.color}`}>
              {((trendsData?.summary?.average_sentiment || 0) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Avg Sentiment</div>
          </div>
        </div>

        {/* Sentiment Trend Chart */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Sentiment Trend</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formatChartData(trendsData?.trends || [])}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="time" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `T${value}`}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  domain={[-100, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip 
                  formatter={(value, name) => [`${value}%`, 'Sentiment']}
                  labelFormatter={(label) => `Time ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="sentiment" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Distribution */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Sentiment Distribution</h4>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={formatPieData(trendsData?.summary?.sentiment_distribution || {})}
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={60}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {formatPieData(trendsData?.summary?.sentiment_distribution || {}).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex justify-center space-x-4 mt-2">
            {formatPieData(trendsData?.summary?.sentiment_distribution || {}).map((entry) => (
              <div key={entry.name} className="flex items-center space-x-1">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                ></div>
                <span className="text-xs text-gray-600">
                  {entry.name} ({entry.value})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Articles with Sentiment */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Articles</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {(trendsData?.trends || []).slice(0, 3).map((article, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {article.title}
                  </div>
                  <div className="text-gray-500">
                    {article.ticker} • {(article.sentiment_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                  article.sentiment_score > 0.1 
                    ? 'bg-green-100 text-green-800' 
                    : article.sentiment_score < -0.1 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {article.sentiment_score > 0.1 ? 'Positive' : article.sentiment_score < -0.1 ? 'Negative' : 'Neutral'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SentimentPanel;
