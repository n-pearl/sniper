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
    if (!trends || trends.length === 0) return [];
    
    return trends.slice(0, 20).map((item, index) => ({
      time: new Date(item.published_at).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      sentiment: (item.sentiment_score * 100).toFixed(1),
      rawScore: item.sentiment_score,
      title: item.title.substring(0, 50) + '...',
      ticker: item.ticker || 'N/A'
    }));
  };

  const formatPieData = (summary) => {
    if (!summary || !summary.sentiment_distribution) {
      return [
        { name: 'Positive', value: 0, color: '#10B981' },
        { name: 'Negative', value: 0, color: '#EF4444' },
        { name: 'Neutral', value: 0, color: '#6B7280' }
      ];
    }
    
    const distribution = summary.sentiment_distribution;
    return [
      { name: 'Positive', value: distribution.positive || 0, color: '#10B981' },
      { name: 'Negative', value: distribution.negative || 0, color: '#EF4444' },
      { name: 'Neutral', value: distribution.neutral || 0, color: '#6B7280' }
    ];
  };

  const getSentimentTrend = (average) => {
    if (average > 0.1) return { direction: 'up', color: 'text-green-600', icon: TrendingUp };
    if (average < -0.1) return { direction: 'down', color: 'text-red-600', icon: TrendingDown };
    return { direction: 'neutral', color: 'text-gray-600', icon: Activity };
  };

  const getSentimentSummary = () => {
    if (!trendsData || !trendsData.summary) {
      return {
        total_articles: 0,
        average_sentiment: 0,
        sentiment_distribution: { positive: 0, negative: 0, neutral: 0 }
      };
    }
    return trendsData.summary;
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 p-6 border border-gray-200 dark:border-dark-700">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-dark-600 rounded w-1/2 mb-4"></div>
          <div className="h-64 bg-gray-200 dark:bg-dark-600 rounded mb-4"></div>
          <div className="h-32 bg-gray-200 dark:bg-dark-600 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 p-6 border border-gray-200 dark:border-dark-700">
        <div className="text-center text-red-600 dark:text-red-400">
          <p className="mb-2">⚠️ {error}</p>
          <button 
            onClick={fetchSentimentTrends}
            className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = getSentimentSummary();
  const trend = getSentimentTrend(summary.average_sentiment);
  const TrendIcon = trend.icon;
  const chartData = formatChartData(trendsData?.trends || []);
  const pieData = formatPieData(summary);

  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 border border-gray-200 dark:border-dark-700 transition-all duration-300">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Sentiment Analysis</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Market sentiment trends and distribution
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <TrendIcon className={`h-5 w-5 ${trend.color}`} />
            <span className={`text-sm font-medium ${trend.color}`}>
              {trend.direction === 'up' ? 'Bullish' : trend.direction === 'down' ? 'Bearish' : 'Neutral'}
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Ticker:</span>
            <input
              type="text"
              placeholder="Filter by ticker..."
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="text-sm border border-gray-300 dark:border-dark-600 rounded px-2 py-1 w-24 bg-white dark:bg-dark-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Range:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="text-sm border border-gray-300 dark:border-dark-600 rounded px-2 py-1 bg-white dark:bg-dark-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            >
              <option value={6}>6 hours</option>
              <option value={12}>12 hours</option>
              <option value={24}>24 hours</option>
              <option value={72}>3 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {summary.total_articles || 0}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Total Articles</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
            <div className={`text-2xl font-bold ${trend.color}`}>
              {((summary.average_sentiment || 0) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Avg Sentiment</div>
          </div>
        </div>

        {/* Sentiment Trend Chart */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Sentiment Over Time</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" className="dark:stroke-dark-600" />
                <XAxis 
                  dataKey="time" 
                  tick={{ fontSize: 12, fill: 'currentColor' }}
                  tickFormatter={(value) => value}
                  className="text-gray-600 dark:text-gray-400"
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: 'currentColor' }}
                  className="text-gray-600 dark:text-gray-400"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--tooltip-bg)', 
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '8px',
                    color: 'var(--tooltip-text)'
                  }}
                  formatter={(value, name) => [`${value}%`, 'Sentiment']}
                  labelFormatter={(label) => `Time: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="sentiment" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#2563eb' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Distribution */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Sentiment Distribution</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--tooltip-bg)', 
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '8px',
                    color: 'var(--tooltip-text)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex justify-center space-x-4 mt-2">
            {pieData.map((entry) => (
              <div key={entry.name} className="flex items-center space-x-1">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                ></div>
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  {entry.name}: {entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SentimentPanel;
