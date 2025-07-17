import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import NewsFeed from './components/NewsFeed';
import SentimentPanel from './components/SentimentPanel';
import ArchiveLookup from './components/ArchiveLookup';
import { BarChart3, Newspaper, Search, TrendingUp, Moon, Sun } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-dark-900 transition-colors duration-300">
          <AppContent />
        </div>
      </Router>
    </ThemeProvider>
  );
}

function AppContent() {
  const { isDarkMode, toggleTheme } = useTheme();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ctrl/Cmd + D for dark mode toggle
      if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
        event.preventDefault();
        toggleTheme();
      }
      
      // Ctrl/Cmd + R for refresh (prevent default and show custom message)
      if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        window.location.reload();
      }
      
      // Escape to clear all filters (if on dashboard)
      if (event.key === 'Escape' && window.location.pathname === '/') {
        // This will be handled by individual components
        const event = new CustomEvent('clearFilters');
        window.dispatchEvent(event);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleTheme]);

  return (
    <>
      {/* Header */}
      <header className="bg-white dark:bg-dark-800 shadow-sm border-b border-gray-200 dark:border-dark-700 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <h1 className="ml-3 text-xl font-bold text-gray-900 dark:text-white">
                Sniper News Intelligence
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <nav className="flex space-x-8">
                <a href="/" className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Dashboard
                </a>
                <a href="/archive" className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Archive
                </a>
              </nav>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
                aria-label="Toggle theme"
                title={`Switch to ${isDarkMode ? 'light' : 'dark'} mode (Ctrl+D)`}
              >
                {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/archive" element={<ArchiveLookup />} />
        </Routes>
      </main>

      {/* Keyboard Shortcuts Help */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className="bg-white dark:bg-dark-800 rounded-lg shadow-lg border border-gray-200 dark:border-dark-700 p-3 text-xs text-gray-600 dark:text-gray-400 max-w-xs opacity-75 hover:opacity-100 transition-opacity">
          <div className="font-medium mb-1">Keyboard Shortcuts:</div>
          <div>Ctrl+D: Toggle theme</div>
          <div>Ctrl+R: Refresh</div>
          <div>Esc: Clear filters</div>
        </div>
      </div>
    </>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({
    total_articles: 0,
    processed_articles: 0,
    processing_rate: 0,
    average_sentiment: 0,
    top_tickers: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/news/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      // Keep existing stats on error
    } finally {
      setLoading(false);
    }
  };

  const formatSentimentValue = (value) => {
    return value > 0 ? `+${(value * 100).toFixed(1)}` : `${(value * 100).toFixed(1)}`;
  };

  const getSentimentChangeType = (value) => {
    return value >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className="space-y-6 lg:space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="animate-slide-up">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-2">
              News Intelligence Dashboard
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm lg:text-base">
              Real-time financial news analysis and sentiment tracking
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs lg:text-sm text-gray-500 dark:text-gray-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Live</span>
            </div>
            <span className="text-xs lg:text-sm text-gray-500 dark:text-gray-400">
              Last updated: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 animate-slide-up">
        <StatCard
          title="Total Articles"
          value={loading ? "..." : stats.total_articles.toLocaleString()}
          change={loading ? "..." : `+${stats.processed_articles}`}
          changeType="positive"
          icon={Newspaper}
          loading={loading}
        />
        <StatCard
          title="Avg Sentiment"
          value={loading ? "..." : formatSentimentValue(stats.average_sentiment)}
          change={loading ? "..." : formatSentimentValue(stats.average_sentiment)}
          changeType={getSentimentChangeType(stats.average_sentiment)}
          icon={TrendingUp}
          loading={loading}
        />
        <StatCard
          title="Processing Rate"
          value={loading ? "..." : `${stats.processing_rate.toFixed(1)}%`}
          change={loading ? "..." : `${stats.processed_articles}/${stats.total_articles}`}
          changeType="positive"
          icon={BarChart3}
          loading={loading}
        />
        <StatCard
          title="Active Tickers"
          value={loading ? "..." : stats.top_tickers.length}
          change={loading ? "..." : `Top: ${stats.top_tickers[0]?.ticker || 'N/A'}`}
          changeType="positive"
          icon={Search}
          loading={loading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8 animate-slide-up">
        {/* News Feed - Takes 2/3 of the width on large screens */}
        <div className="xl:col-span-2 order-2 xl:order-1">
          <NewsFeed />
        </div>
        
        {/* Sentiment Panel - Takes 1/3 of the width on large screens */}
        <div className="xl:col-span-1 order-1 xl:order-2">
          <SentimentPanel />
        </div>
      </div>

      {/* Additional Analytics Section */}
      <div className="animate-slide-up">
        <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 border border-gray-200 dark:border-dark-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Quick Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {loading ? "..." : stats.top_tickers.slice(0, 3).map(t => t.ticker).join(", ") || "N/A"}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Most Mentioned</div>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {loading ? "..." : "24h"}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Data Range</div>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {loading ? "..." : "Real-time"}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Update Frequency</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, change, changeType, icon: Icon, loading }) {
  return (
    <div className="bg-white dark:bg-dark-800 rounded-lg shadow-sm dark:shadow-dark-900/10 p-4 lg:p-6 hover:shadow-md dark:hover:shadow-dark-900/20 transition-all duration-300 border border-gray-200 dark:border-dark-700 group">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 lg:h-8 lg:w-8 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform duration-300" />
        </div>
        <div className="ml-3 lg:ml-4 min-w-0 flex-1">
          <p className="text-xs lg:text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{title}</p>
          <p className="text-lg lg:text-2xl font-semibold text-gray-900 dark:text-white truncate">
            {loading ? (
              <div className="animate-pulse bg-gray-300 dark:bg-dark-600 h-6 lg:h-8 rounded w-16"></div>
            ) : (
              value
            )}
          </p>
        </div>
      </div>
      <div className="mt-3 lg:mt-4">
        <span className={`inline-flex items-center px-2 lg:px-2.5 py-0.5 rounded-full text-xs font-medium ${
          changeType === 'positive' 
            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
        }`}>
          {loading ? (
            <div className="animate-pulse bg-gray-300 dark:bg-dark-600 h-3 rounded w-12"></div>
          ) : (
            change
          )}
        </span>
        <span className="ml-2 text-xs lg:text-sm text-gray-500 dark:text-gray-400">from last hour</span>
      </div>
    </div>
  );
}

export default App;
