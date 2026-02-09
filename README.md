# AI Chat System

A production-quality full-stack AI chat system built with React, FastAPI, and LangChain ReAct agent. Features real-time streaming responses, web search capabilities, Google Trends integration, and secure authentication.

## Architecture

- **Frontend**: React + TypeScript with Tailwind CSS
- **Backend**: FastAPI with Python
- **AI Agent**: LangChain ReAct with OpenAI
- **Tools**: Tavily Search + Google Trends MCP
- **Database/Auth**: Supabase with Row Level Security
- **Streaming**: Server-Sent Events (SSE)
- **Infrastructure**: Docker Compose

## Features

- 🔐 Secure Supabase email/password authentication
- 💬 Real-time streaming chat responses
- 🔍 Web search integration via Tavily
- 📊 Google Trends analysis via MCP
- 🧠 LangChain ReAct agent with tool orchestration
- 💾 Persistent chat history and conversations
- 🔒 Row-level security for user data isolation
- 🐳 Docker containerized deployment
- 📱 Responsive modern UI

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd google-news-trends-mcp
```

### 2. Environment Configuration

Copy the environment example files and configure your credentials:

```bash
# Root environment
cp .env.example .env

# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

Edit the `.env` files with your actual credentials:

- **Supabase**: Create a project at [supabase.com](https://supabase.com)
- **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Tavily**: Get API key from [tavily.com](https://tavily.com)
- **Google Trends MCP**: Configure JWT secret

### 3. Database Setup

Apply the Supabase schema:

```bash
# Apply the schema to your Supabase project
psql -h YOUR_DB_HOST -U postgres -d postgres -f supabase_schema.sql
```

Or use the Supabase SQL editor to run the contents of `supabase_schema.sql`.

### 4. Start with Docker

```bash
docker-compose up --build
```

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Google Trends MCP: http://localhost:8001
- API Documentation: http://localhost:8000/docs

## Development

### Local Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Local Frontend Development

```bash
cd frontend
npm install
npm start
```

### Local Google Trends MCP

```bash
cd google-news-trends-mcp
pip install -e .
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Chat Endpoints

- `POST /api/chat/stream` - Send message and stream response (SSE)
- `GET /api/chat/conversations` - Get user conversations
- `GET /api/chat/conversations/{id}/messages` - Get conversation messages

### Health Endpoints

- `GET /api/health` - Basic health check
- `GET /api/health/dependencies` - Check service dependencies

## Security Features

- **JWT Authentication**: Supabase JWT tokens with validation
- **Row Level Security**: Users can only access their own data
- **CORS Protection**: Configured for frontend domain
- **Input Validation**: Pydantic schemas for all inputs
- **Error Handling**: No stack traces exposed to clients
- **API Key Protection**: No keys logged or exposed

## Agent Capabilities

The LangChain ReAct agent can:

1. **Search the Web**: Use Tavily to find current information
2. **Analyze Trends**: Access Google Trends data via MCP
3. **Reason and Plan**: Use ReAct methodology for complex queries
4. **Tool Orchestration**: Chain multiple tools for comprehensive answers
5. **Graceful Fallbacks**: Handle tool failures gracefully

## Docker Services

- **backend**: FastAPI application (port 8000)
- **frontend**: React development server (port 3000)
- **google-trends-mcp**: Google Trends MCP server (port 8001)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)

## Environment Variables

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# AI Services
OPENAI_API_KEY=your-openai-key
TAVILY_API_KEY=your-tavily-key

# MCP
GOOGLE_TRENDS_MCP_URL=http://google-trends-mcp:8000/mcp
GOOGLE_TRENDS_MCP_JWT_SECRET=your-mcp-secret

# App
SECRET_KEY=your-app-secret
ALGORITHM=HS256
```

### Frontend (.env)

```bash
REACT_APP_API_URL=http://localhost:8000
```

## Production Deployment

1. **Update Environment**: Set `ENVIRONMENT=production` and `DEBUG=false`
2. **Configure URLs**: Update frontend API URL to production domain
3. **SSL/TLS**: Configure SSL certificates
4. **Database**: Use production Supabase instance
5. **Monitoring**: Set up health checks and monitoring

## Troubleshooting

### Common Issues

1. **Docker Build Failures**: Check Docker logs and ensure all dependencies are installed
2. **Database Connection**: Verify Supabase credentials and network access
3. **MCP Connection**: Ensure Google Trends MCP service is running and accessible
4. **Authentication**: Check JWT secrets are consistent across services

### Health Checks

```bash
# Check all services
curl http://localhost:8000/api/health/dependencies

# Check individual services
curl http://localhost:8000/api/health
curl http://localhost:8001/healthz
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review Docker logs: `docker-compose logs`
- Check API documentation at `/docs` endpoint
