# rag_utils.py
import json
import os
from typing import List, Tuple

import openai
from qdrant_client import QdrantClient

from models import (
    ApiResponse,
    ChatMessage,
    RawSource,
    SuggestQuestionsRequest,
    SuggestQuestionsResponse,
    UserQuery,
    ValidatedSource,
)
from prompts import (
    REWRITE_PROMPT,
    REWRITE_SUGGESTION_QUESTION_PROMPT,
    SUGGEST_QUESTIONS_PROMPT,
    SYSTEM_PROMPT,
)

# --- Client initializations ---
client = openai.AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

qdrant_client = QdrantClient("http://localhost:6333")
QDRANT_COLLECTION_NAME = "Connect_Investigation_Training_Manual_v25.0"
document = "Connect Investigation Training Manual v25.0.pdf"

def ask_rag(query: UserQuery) -> ApiResponse:
    case_context_str = _format_case_context(query.case_context)
    standalone_question = _get_standalone_question(query, case_context_str)
    print(f"Original Question: '{query.question}'")
    print(f"Case Context: {case_context_str}")
    print(f"Standalone Question for Search: '{standalone_question}'")

    question_embedding = _get_question_embedding(standalone_question)
    search_result = _search_qdrant(question_embedding, query.top_k)
    context, rawSources = _prepare_context_and_raw_sources(search_result)
    final_prompt = _build_final_prompt(query, case_context_str, context)
    raw_output = _get_llm_response(final_prompt)
    return _parse_and_validate_output(raw_output, standalone_question, rawSources)

def _get_standalone_question(query, case_context_str):
    if getattr(query, "history", None) or case_context_str.strip():
        chat_history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in getattr(query, "history", [])])
        rewrite_prompt = REWRITE_PROMPT.format(
            chat_history=chat_history_str,
            case_context=case_context_str,
            question=query.question
        )
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.0,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    return query.question

def _get_question_embedding(question):
    return client.embeddings.create(
        input=[question],
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    ).data[0].embedding

def _search_qdrant(question_embedding, top_k):
    return qdrant_client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=question_embedding,
        limit=top_k,
        with_payload=True
    )

def _prepare_context_and_raw_sources(search_result):
    context = ""
    rawSources = []
    for r in search_result:
        p = r.payload
        similarity = float(r.score)
        context += (
            f"Source (Section {p.get('section_number','N/A')}, Title: {p.get('section_title','')}, "
            f"Score: {similarity:.4f}):\n{p.get('content','')}\n\n"
        )
        rawSources.append(RawSource(            
            document=document,
            section_number=p.get("section_number", "N/A"),
            section_title=p.get("section_title", "N/A"),
            page_number=p.get("page_number", -1),
            chunk=p.get("content", ""),
            similarity_score=similarity
        ))
    return context, rawSources

def _build_final_prompt(query, case_context_str, context):
    conversation_history_for_prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in getattr(query, "history", [])])
    return (
        f"CONVERSATION HISTORY:\n---\n{conversation_history_for_prompt}\n---\n\n"
        f"CURRENT CASE CONTEXT:\n---\n{case_context_str}\n---\n\n"
        f"CONTEXT FROM MANUAL:\n---\n{context}\n---\n\n"
        f"USER'S LATEST QUESTION: {query.question}\n\n"
        "Based on all the provided information (history, case context, and manual context), "
        "please answer the user's latest question and provide the response in the required JSON format."
    )

def _get_llm_response(final_prompt):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content.strip()

def _parse_and_validate_output(raw_output, standalone_question, rawSources):
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return ApiResponse(
            question=standalone_question,
            answer="The system generated an invalid response. Please try rephrasing your question.",
            validated_sources=[],
            raw_sources=[rs.dict() for rs in rawSources]
        )

    # Accept either camelCase or snake_case from the LLM
    answer_text = parsed.get("answer", parsed.get("answer", "")).strip()
    validated_sources_from_llm = parsed.get("validatedSources", parsed.get("validated_sources", []))

    # Fallback: If answer exists but no validated sources, cite all raw sources
    if answer_text and "does not contain information" not in answer_text.lower() and not validated_sources_from_llm:
        print("LOG: LLM provided an answer but no validated sources. Applying fallback to cite all raw sources.")
        validated_sources_from_llm = [
            {
                "document": rs.document,
                "section_number": rs.section_number,
                "section_title": rs.section_title,
                "page_number": rs.page_number,
                "similarity_score": rs.similarity_score,
            }
            for rs in rawSources
        ]

    # Final validation: Use trusted rawSources data for validatedSources
    final_validated_sources = []
    raw_sources_map = {rs.section_number: rs for rs in rawSources}
    for vs_data in validated_sources_from_llm:
        section_num = vs_data.get("section_number") or vs_data.get("sectionNumber")
        if section_num in raw_sources_map:
            matched_raw_source = raw_sources_map[section_num]
            final_validated_sources.append(ValidatedSource(
                document=matched_raw_source.document,
                section_number=matched_raw_source.section_number,
                section_title=matched_raw_source.section_title,
                page_number=matched_raw_source.page_number,
                similarity_score=matched_raw_source.similarity_score,
            ))

    return ApiResponse(
        question=standalone_question,
        answer=answer_text,
        validated_sources=final_validated_sources,
        # raw_sources=rawSources,
    )

def suggest_questions(request: SuggestQuestionsRequest) -> SuggestQuestionsResponse:
    case_context_str = _format_case_context(request.case_context)
    standalone_question = _rewrite_suggestion_question(case_context_str)
    print(f"Case Context: {case_context_str}")
    print(f"Standalone Question for Search: '{standalone_question}'")

    question_embedding = _get_question_embedding(standalone_question)
    search_result = _search_qdrant(question_embedding, request.top_k)
    # build manual_content and rawSources for the response
    manual_content = _build_manual_content(search_result)
    suggestion_raw_sources = []
    for r in search_result:
        p = r.payload
        similarity = float(r.score)
        suggestion_raw_sources.append(RawSource(          
            document=document,
            section_number=p.get("section_number", "N/A"),
            section_title=p.get("section_title", "N/A"),
            page_number=p.get("page_number", -1),
            chunk=p.get("content", ""),
            similarity_score=similarity
        ))
    prompt = SUGGEST_QUESTIONS_PROMPT.format(
        case_context=case_context_str,
        manual_content=manual_content,
        top_k=request.top_k
    )
    raw_output = _get_suggest_questions_llm_response(prompt)
    questions = _parse_suggested_questions(raw_output)
    return SuggestQuestionsResponse(
        question=standalone_question,
        suggested_questions=questions,
        # raw_sources=suggestion_raw_sources,
    )

def _rewrite_suggestion_question(case_context_str):
    if case_context_str.strip():
        rewrite_prompt = REWRITE_SUGGESTION_QUESTION_PROMPT.format(
            formatted_case_context=case_context_str
        )
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.0,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    return ""

def _build_manual_content(search_result):
    return "\n".join([
        f"Section {r.payload.get('section_number', '')}: {r.payload.get('content', '')}"
        for r in search_result
    ])

def _get_suggest_questions_llm_response(prompt):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def _parse_suggested_questions(raw_output):
    questions = []
    for line in raw_output.split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            q = line.split('.', 1)[-1].strip() if '.' in line else line.lstrip('-').strip()
            if q:
                questions.append(q)
    return questions

def _format_case_context(case_context) -> str:
    """Helper function to format the case context object into a string."""
    if not case_context:
        return "No case details provided."

    context_parts = []
    if getattr(case_context, "case_type", None):
        context_parts.append(f"- Case Type: {case_context.case_type}")
    if getattr(case_context, "case_summary", None):
        context_parts.append(f"- Summary: {case_context.case_summary}")
    if getattr(case_context, "involved_entities", None):
        entities_str = ", ".join(case_context.involved_entities)
        context_parts.append(f"- Involved Entities: {entities_str}")

    return "\n".join(context_parts) if context_parts else "No case details provided."