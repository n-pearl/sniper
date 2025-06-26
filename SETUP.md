# Sniper Setup Guide

## Initial Repository Setup

### 1. Create .env file
Copy the environment variables from `env.example` to `.env`:

```bash
cp env.example .env
```

**IMPORTANT**: The `.env` file contains your actual API keys and should never be committed to git.

### 2. Update API Keys
Edit the `.env` file and replace the placeholder API keys with your actual keys:

```bash
# Get your Alpha Vantage API key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_actual_alpha_vantage_key

# Get your OpenAI API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_actual_openai_key
```

### 3. Initialize Git Repository

```bash
# Initialize git repository
git init

# Add all files (except those in .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: Sniper News Intelligence Engine"

# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/sniper.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Environment Variables

The following environment variables are used throughout the application:

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port

### API Keys
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key for news data
- `OPENAI_API_KEY`: OpenAI API key for sentiment analysis

### Application Settings
- `APP_NAME`: Application name
- `DEBUG`: Debug mode (true/false)
- `API_V1_STR`: API version string

### Sentiment Analysis
- `SENTIMENT_BATCH_SIZE`: Batch size for sentiment processing
- `FINBERT_MODEL_NAME`: FinBERT model name

### News Processing
- `NEWS_UPDATE_INTERVAL`: News update interval in seconds
- `MAX_ARTICLES_PER_REQUEST`: Maximum articles per API request

### Frontend
- `VITE_API_BASE_URL`: Backend API base URL

## Security Notes

1. **Never commit `.env` files** - They contain sensitive API keys
2. **Use environment variables in production** - Set them in your deployment platform
3. **Rotate API keys regularly** - Especially if they're exposed
4. **Use different keys for development and production**

## Production Deployment

For production deployment, set the environment variables in your hosting platform:

- **Railway**: Use the Railway dashboard to set environment variables
- **Heroku**: Use `heroku config:set KEY=value`
- **Docker**: Use `--env-file` or environment variables
- **Kubernetes**: Use ConfigMaps and Secrets

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are valid and have sufficient credits
2. **Database Connection**: Check PostgreSQL is running and credentials are correct
3. **Port Conflicts**: Ensure ports 8000 (backend) and 3000 (frontend) are available

### Getting API Keys

- **Alpha Vantage**: Sign up at https://www.alphavantage.co/
- **OpenAI**: Sign up at https://platform.openai.com/ 