# Sniper News Intelligence Engine

A standalone real-time and historical financial news intelligence engine that powers the News Dashboard for a potential agentic trading system. Sniper provides advanced sentiment analysis, vector search capabilities, and market impact correlation analysis.

## 🚀 Features

- **Real-time News Ingestion**: Integrates with Alpha Vantage APIs for live financial news
- **Advanced Sentiment Analysis**: Ensemble approach using FinBERT + OpenAI for accurate sentiment scoring
- **Vector Search**: PostgreSQL with pgvector for semantic similarity search
- **Time-series Analytics**: TimescaleDB for efficient historical data analysis
- **Market Impact Correlation**: Track sentiment-price relationships over time
- **Modern Web Interface**: React + Tailwind CSS dashboard with real-time updates
- **Modular Architecture**: Designed for easy integration with Daygent trading system

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│                 │    │                 │    │   + TimescaleDB │
│ - NewsFeed      │    │ - News Service  │    │   + pgvector    │
│ - SentimentPanel│    │ - Sentiment     │    │                 │
│ - ArchiveLookup │    │   Engine        │    │                 │
└─────────────────┘    │ - API Routes    │    └─────────────────┘
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   External      │
                       │   Services      │
                       │                 │
                       │ - Alpha Vantage │
                       │ - OpenAI API    │
                       └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Primary database with TimescaleDB and pgvector extensions
- **Redis**: Caching and message broker for Celery
- **Celery**: Asynchronous task processing
- **FinBERT**: Financial sentiment analysis model
- **OpenAI API**: Advanced language model integration

### Frontend
- **React 18**: Modern UI framework
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Data visualization library
- **Axios**: HTTP client for API communication

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **TimescaleDB**: Time-series database extension
- **pgvector**: Vector similarity search

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- Alpha Vantage API key
- OpenAI API key

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sniper
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Start PostgreSQL with Docker
   docker run -d --name sniper-postgres \
     -e POSTGRES_DB=sniper \
     -e POSTGRES_USER=user \
     -e POSTGRES_PASSWORD=password \
     -p 5432:5432 \
     timescale/timescaledb:latest-pg14
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Run Backend**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sniper
POSTGRES_DB=sniper
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
OPENAI_API_KEY=your_openai_key

# Redis
REDIS_URL=redis://localhost:6379

# App Settings
DEBUG=true
API_V1_STR=/api/v1
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/news/` | GET | Get recent news articles |
| `/api/v1/news/fetch` | POST | Fetch and process news from Alpha Vantage |
| `/api/v1/news/company/{symbol}` | GET | Get company-specific news |
| `/api/v1/news/sentiment/trends` | GET | Get sentiment trends over time |
| `/api/v1/news/search/similar` | GET | Search similar articles |
| `/api/v1/news/stats` | GET | Get news statistics |
| `/api/v1/news/process/{article_id}` | POST | Reprocess article sentiment |

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📊 Usage

### Dashboard Overview
The main dashboard provides:
- **Real-time News Feed**: Live financial news with sentiment indicators
- **Sentiment Analysis Panel**: Trends, distributions, and correlations
- **Archive Search**: Historical news lookup with advanced filtering

### Key Features

1. **News Ingestion**
   - Automatic fetching from Alpha Vantage
   - Real-time sentiment analysis
   - Duplicate detection and deduplication

2. **Sentiment Analysis**
   - Ensemble approach (FinBERT + OpenAI)
   - Confidence scoring
   - Vector embeddings for similarity search

3. **Market Impact Tracking**
   - Sentiment-price correlation analysis
   - Time-series trend identification
   - Impact scoring algorithms

4. **Search & Filtering**
   - Full-text search across articles
   - Sentiment-based filtering
   - Ticker symbol filtering
   - Date range selection

## 🔄 Integration with Daygent

Sniper is designed as a modular component that can be cleanly integrated into the larger Daygent trading system:

1. **API Integration**: RESTful APIs for data access
2. **Event Streaming**: Real-time sentiment updates
3. **Data Export**: Structured data formats for trading algorithms
4. **Configuration Management**: Centralized settings for trading strategies

## 🚀 Deployment

### Production Deployment
```bash
# Build and deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to cloud platforms
# - AWS ECS
# - Google Cloud Run
# - Azure Container Instances
```

### RunPod Integration
For async scoring jobs on RunPod:
```bash
# Deploy Celery workers to RunPod
docker build -t sniper-worker ./backend
docker push your-registry/sniper-worker

# Configure RunPod endpoints for:
# - Sentiment analysis tasks
# - Batch processing jobs
# - Model inference
```

## 📈 Performance

- **News Processing**: ~1000 articles/hour
- **Sentiment Analysis**: ~50ms per article (ensemble)
- **Vector Search**: Sub-second similarity queries
- **Real-time Updates**: <5 second latency

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the troubleshooting guide

## 🔮 Roadmap

- [ ] Advanced market impact modeling
- [ ] Multi-language sentiment analysis
- [ ] Real-time alerting system
- [ ] Advanced backtesting capabilities
- [ ] Machine learning model training pipeline
- [ ] Integration with additional news sources
- [ ] Mobile application
- [ ] Advanced visualization dashboards 
