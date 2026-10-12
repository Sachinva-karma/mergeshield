from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.analyzer import PRAnalyzerService
from app.config import get_settings
from app.github_client import GitHubClientError
from app.model_adapter import ModelProviderError
from app.schemas import AnalysisResponse, PRAnalyzeRequest

app = FastAPI(
    title="MergeShield API",
    description="Evidence-backed public GitHub Pull Request risk auditor powered by open-weight models.",
    version="1.0.0",
)

# Enable CORS for local development & frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer_service = PRAnalyzerService()


@app.get("/api/health")
def health_check():
    settings = get_settings()
    has_model_key = bool(settings.get_model_api_key())
    has_github_token = bool(settings.get_github_token())

    return {
        "status": "healthy",
        "service": "MergeShield API",
        "model_provider": settings.MODEL_PROVIDER,
        "model_name": settings.MODEL_NAME,
        "is_model_configured": has_model_key,
        "is_github_token_configured": has_github_token,
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_pull_request(request: PRAnalyzeRequest):
    try:
        result = await analyzer_service.analyze_pr_url(request.pr_url)
        return result
    except GitHubClientError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except ModelProviderError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error during PR analysis: {str(e)}",
        )
