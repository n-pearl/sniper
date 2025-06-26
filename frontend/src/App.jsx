import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NewsFeed from './components/NewsFeed';
import SentimentPanel from './components/SentimentPanel';
import ArchiveLookup from './components/ArchiveLookup';
import { BarChart3, Newspaper, Search, TrendingUp } from 'lucide-react';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-blue-600" />
                <h1 className="ml-3 text-xl font-bold text-gray-900">
                  Sniper News Intelligence
                </h1>
              </div>
              <nav className="flex space-x-8">
                <a href="/" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </a>
                <a href="/archive" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Archive
                </a>
              </nav>
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
      </div>
    </Router>
  );
}

function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          News Intelligence Dashboard
        </h2>
        <p className="text-gray-600">
          Real-time financial news analysis and sentiment tracking
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total Articles"
          value="1,234"
          change="+12%"
          changeType="positive"
          icon={Newspaper}
        />
        <StatCard
          title="Avg Sentiment"
          value="0.23"
          change="+0.05"
          changeType="positive"
          icon={TrendingUp}
        />
        <StatCard
          title="Processing Rate"
          value="98.5%"
          change="+2.1%"
          changeType="positive"
          icon={BarChart3}
        />
        <StatCard
          title="Active Tickers"
          value="45"
          change="+3"
          changeType="positive"
          icon={Search}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* News Feed - Takes 2/3 of the width */}
        <div className="lg:col-span-2">
          <NewsFeed />
        </div>
        
        {/* Sentiment Panel - Takes 1/3 of the width */}
        <div className="lg:col-span-1">
          <SentimentPanel />
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, change, changeType, icon: Icon }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-8 w-8 text-blue-600" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
      <div className="mt-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          changeType === 'positive' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {change}
        </span>
        <span className="ml-2 text-sm text-gray-500">from last hour</span>
      </div>
    </div>
  );
}

export default App;
