# M32 Business Intelligence Copilot

A business intelligence chatbot that helps SMB owners make better decisions using AI.

## What it does

- Market research and competitor analysis
- Business strategy recommendations  
- Industry insights and trends
- Real-time web search for business data

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + TypeScript + Tailwind CSS
- **AI**: Groq API with open-source models (Mixtral, Llama)

## Quick Start

### 1. Get your Groq API key
Sign up at [console.groq.com](https://console.groq.com) and get your free API key.

### 2. Setup environment
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your API key
GROQ_API_KEY=your_api_key_here
```

### 3. Run with Docker (easiest)
```bash
docker-compose up -d
```

### 4. Or run manually

**Backend:**
```bash
pip install -r requirements.txt
python backend/main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Access the app

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Sample .env file

```bash
# Required
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional (these are the defaults)
GROQ_MODEL_NAME=mixtral-8x7b-32768
MAX_TOKENS=1024
TEMPERATURE=0.7
DEBUG=true
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite:///./m32_business_copilot.db
```

## Available Models

- `mixtral-8x7b-32768` - Best balance of speed/quality (default)
- `llama2-70b-4096` - Higher quality, slower
- `gemma-7b-it` - Faster, good for simple tasks

## Features

- User authentication with JWT
- Chat sessions with conversation history
- Business context awareness
- Real-time AI responses
- Market research tools
- Competitor analysis
- Industry insights

## Project Structure

```
├── backend/          # FastAPI backend
├── frontend/         # React frontend  
├── ai-core/          # AI integration
├── tools/            # Business intelligence tools
├── docs/             # Documentation
└── deployment/       # Docker configs
```

## Development

The app uses SQLite for development (no setup needed) and can be configured for PostgreSQL in production.

All AI responses are powered by Groq's fast inference API using open-source models, making it much cheaper than OpenAI while maintaining good quality.

## License

MIT