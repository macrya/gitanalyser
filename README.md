# GitHub Technical Debt Analyzer

A comprehensive web application that analyzes GitHub repositories for technical debt, provides specific code improvement suggestions, and generates automated refactoring pull requests.

## Features

- **Automated Code Analysis**: Deep analysis of code quality, complexity, and technical debt patterns
- **GitHub OAuth Integration**: Secure authentication with GitHub
- **Quality Metrics**: Track metrics including cyclomatic complexity, maintainability index, and technical debt ratio
- **Smart Suggestions**: Get specific, actionable code improvement recommendations
- **Automated Refactoring**: Generate pull requests with automated code improvements
- **Security Analysis**: Identify potential security vulnerabilities using Bandit
- **Multi-Language Support**: Analyze Python, JavaScript, and TypeScript projects
- **Beautiful Dashboard**: Visualize code quality metrics and track improvements over time

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PyGithub**: GitHub API integration
- **GitPython**: Git repository manipulation
- **Radon**: Code complexity analysis
- **Bandit**: Security vulnerability scanning

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Composable charting library
- **Axios**: HTTP client

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Redis**: Caching and task queue
- **Alembic**: Database migrations

## Prerequisites

- Docker and Docker Compose
- GitHub OAuth App credentials
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/gitanalyser.git
cd gitanalyser
```

### 2. Set Up GitHub OAuth App

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Fill in the details:
   - **Application name**: GitHub Technical Debt Analyzer
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/auth/callback`
4. Copy the Client ID and generate a Client Secret

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Backend
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=gitanalyser

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback

# JWT Secret (generate a secure random string)
SECRET_KEY=your-secret-key-min-32-characters-long

# Redis
REDIS_URL=redis://redis:6379/0
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start the Application

```bash
docker-compose up --build
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Initialize the Database

In a new terminal, run:

```bash
docker-compose exec backend alembic upgrade head
```

## Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

## Usage

### 1. Sign In

- Visit http://localhost:3000
- Click "Sign in with GitHub"
- Authorize the application

### 2. Sync Repositories

- Click "Sync Repositories" to import your GitHub repos
- Wait for the sync to complete

### 3. Analyze a Repository

- Click "Analyze" on any repository card
- The analysis will run in the background
- You'll be redirected to the results page when complete

### 4. Review Results

The analysis provides:
- **Code Quality Metrics**: Total lines, files, complexity, technical debt ratio
- **Technical Debt Items**: Categorized by severity (critical, high, medium, low)
- **Code Suggestions**: Specific improvements with confidence scores

### 5. Create Refactoring PR

- Click "Create Refactoring PR" on the analysis results page
- The system will automatically:
  - Create a new branch
  - Apply suggested code improvements
  - Create a pull request on GitHub

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI   │─────▶│ PostgreSQL  │
│  Frontend   │      │   Backend   │      │  Database   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   GitHub    │
                     │     API     │
                     └─────────────┘
```

### Database Schema

- **Users**: GitHub user information and access tokens
- **Repositories**: Repository metadata and analysis history
- **Analyses**: Code analysis results and metrics
- **TechnicalDebtItems**: Individual debt issues found
- **CodeSuggestions**: Automated improvement suggestions
- **PullRequests**: Generated PR metadata

## API Endpoints

### Authentication
- `GET /api/auth/github` - Get GitHub OAuth URL
- `POST /api/auth/github/callback` - Handle OAuth callback
- `GET /api/auth/me` - Get current user

### Repositories
- `GET /api/repositories/` - List user repositories
- `POST /api/repositories/sync` - Sync from GitHub
- `GET /api/repositories/{id}` - Get repository details
- `DELETE /api/repositories/{id}` - Delete repository

### Analysis
- `POST /api/analysis/` - Create new analysis
- `GET /api/analysis/{id}` - Get analysis details
- `GET /api/analysis/repository/{id}` - List repository analyses

### Pull Requests
- `POST /api/pull-requests/` - Create PR from analysis
- `GET /api/pull-requests/{id}` - Get PR details
- `GET /api/pull-requests/repository/{id}` - List repository PRs

## Code Analysis Features

### Python Analysis
- Cyclomatic complexity detection
- Maintainability index calculation
- Code smell detection (long functions, too many parameters)
- Security vulnerability scanning (Bandit)
- TODO/FIXME comment tracking

### JavaScript/TypeScript Analysis
- Large file detection
- Console statement detection
- TODO/FIXME comment tracking
- Code quality patterns

### Metrics Calculated
- **Total Lines of Code**: All analyzed code lines
- **Average Complexity**: Mean cyclomatic complexity
- **Maintainability Index**: Overall code maintainability (0-100)
- **Technical Debt Ratio**: Debt items per 1000 lines of code
- **Issue Severity Distribution**: Count by severity level

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

Create a new migration:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Adding New Analysis Rules

1. Edit `backend/app/services/analyzer.py`
2. Add detection logic in appropriate methods
3. Update database models if needed
4. Run migrations

## Deployment

### Production Environment Variables

Update the following for production:

```bash
# Use strong, randomly generated secrets
SECRET_KEY=<64-character-random-string>

# Use production database
POSTGRES_SERVER=your-prod-db-host
POSTGRES_PASSWORD=<strong-password>

# Update OAuth callback URL
GITHUB_REDIRECT_URI=https://yourdomain.com/auth/callback

# Update CORS origins in backend/app/core/config.py
```

### Docker Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Analysis Failures

- Check if the repository is accessible with your GitHub token
- Ensure the repository isn't too large (> 1GB)
- Check backend logs: `docker-compose logs backend`

### GitHub OAuth Issues

- Verify OAuth app credentials in `.env`
- Check callback URL matches your OAuth app settings
- Ensure redirect URI uses correct protocol (http/https)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [PyGithub](https://github.com/PyGithub/PyGithub)
- [Radon](https://radon.readthedocs.io/)
- [Bandit](https://bandit.readthedocs.io/)

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs)
- Review existing issues and discussions

## Roadmap

- [ ] Support for more programming languages (Go, Java, Rust)
- [ ] Custom analysis rules and configuration
- [ ] Team collaboration features
- [ ] Analysis history and trends
- [ ] Integration with CI/CD pipelines
- [ ] Code review automation
- [ ] Technical debt tracking dashboard
- [ ] Email notifications
- [ ] Slack/Discord integration
- [ ] AI-powered code suggestions

---

Built with ❤️ for better code quality
