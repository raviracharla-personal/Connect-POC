from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ApiResponse,
    SuggestQuestionsRequest,
    SuggestQuestionsResponse,
    UserQuery,
)
from rag_utils import ask_rag, suggest_questions

allowed_origins = [
    "http://localhost",  
    "http://localhost:4200",
    "http://localhost:5000"
]

app = FastAPI(
    title="RAG API for Police Manuals",
    description="API that answers questions with validated police manual sources."
)

@app.post("/manual/answers", response_model=ApiResponse)
def ask_question(query: UserQuery):
    return ask_rag(query)

@app.post("/manual/suggest-questions", response_model=SuggestQuestionsResponse)
def suggest_questions_endpoint(request: SuggestQuestionsRequest):
    return suggest_questions(request)

@app.get("/", include_in_schema=False)
def read_root():
    """ A simple health check endpoint. """
    return {"status": "L&D Insights API is running"}

# Add the CORSMiddleware to the application.
# This middleware must be added before you define any routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of origins that are allowed to make requests
    allow_credentials=True,         # Allow cookies to be included in requests
    allow_methods=["*"],            # Allow all standard methods (GET, POST, etc.)
    allow_headers=["*"],            # Allow all headers
)
