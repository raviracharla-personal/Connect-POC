from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class CaseContext(BaseModel):
    case_type: Optional[str] = Field(None, description="The type of case, e.g., 'Road Traffic Collision', 'Domestic Abuse'.")
    case_summary: Optional[str] = Field(None, description="A brief, one-sentence summary of the case.")
    involved_entities: Optional[List[str]] = Field(None, description="A list of key entities, e.g., ['1 victim', '2 witnesses', '1 blue Ford Fiesta'].")

class UserQuery(BaseModel):
    question: str = Field(..., description="The user's latest question.")
    top_k: int = Field(3, description="The number of documents to retrieve.")
    history: List[ChatMessage] = Field(default_factory=list, description="A list of previous user and assistant messages.")
    case_context: Optional[CaseContext] = Field(None, description="Optional details about the current case being worked on.")

class ValidatedSource(BaseModel):
    document: str
    section_number: str
    section_title: str
    page_number: int
    similarity_score: Optional[float] = None

class RawSource(BaseModel):
    document: str
    section_number: str
    section_title: str
    page_number: int
    chunk: str
    similarity_score: float

class ApiResponse(BaseModel):
    question: str
    answer: str
    validated_sources: List[ValidatedSource]
    raw_sources: Optional[List[RawSource]]= Field(default_factory=list)

class SuggestQuestionsRequest(BaseModel):
    case_context: Optional[CaseContext] = None
    top_k: int = 5

class SuggestQuestionsResponse(BaseModel):
    question: str
    suggested_questions: List[str]
    raw_sources: Optional[List[RawSource]] = Field(default_factory=list)