from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
import models
from database import engine
from routers import course, user, authentication, material, chatbot
from migrations import run_migrations

app = FastAPI()

# Run migrations FIRST, before any database operations
# This ensures the schema is up to date before SQLAlchemy tries to query it
print("🚀 Starting application...")
run_migrations()

# Add CORS middleware - Allow all origins for development (update for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler to ensure CORS headers are always set
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure CORS headers are set even on errors.
    Note: HTTPException should be handled by FastAPI's default handler first.
    """
    # Only handle non-HTTPException errors
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        raise exc
    
    print(f"Global exception: {exc}")
    print(traceback.format_exc())
    
    # Return JSON response with CORS headers
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Create tables AFTER migrations (for new databases)
# Existing databases will have karma column from migration above
models.Base.metadata.create_all(engine)

app.include_router(course.router)
app.include_router(user.router)
app.include_router(authentication.router)
app.include_router(material.router)
app.include_router(chatbot.router)
