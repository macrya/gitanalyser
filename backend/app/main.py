from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, repositories, analysis, pull_requests, webhooks

app = FastAPI(
    title="GitHub Technical Debt Analyzer",
    description="Analyze GitHub repositories for technical debt and generate automated refactoring PRs",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(pull_requests.router, prefix="/api/pull-requests", tags=["Pull Requests"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
async def root():
    return {
        "message": "GitHub Technical Debt Analyzer API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "GitHub OAuth Authentication",
            "Code Quality Analysis",
            "Automated PR Generation",
            "Webhook Support",
            "Rate Limiting"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
