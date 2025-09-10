import os
import json
import io
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import openai
import ffmpeg
import azure.cognitiveservices.speech as speechsdk
from datetime import datetime, date, timedelta
import re
import dateparser
from threading import Event
from phrases import PHRASE_LIST
from question_map import QUESTION_MAP

# --- Import our new tools ---
from tools import ALL_TOOLS, TOOL_SCHEMA_MAP
from prompt import SYSTEM_PROMPT
from fastapi.responses import JSONResponse
import re

# Load environment variables from .env file
load_dotenv()

# --- Pydantic Models for Request/Response validation ---
class Message(BaseModel):
    role: str
    content: str

class TextQueryRequest(BaseModel):
    text: str
    history: List[Message] = []

try:
    # --- Azure OpenAI Client Configuration ---
    openai_client = openai.AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("OPENAI_API_VERSION")
    )
    MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")

    # --- Azure Speech Client Configuration ---
    speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv("AZURE_SPEECH_KEY"),
        region=os.getenv("AZURE_SPEECH_REGION")
    )
except Exception as e:
    print(f"Error configuring Azure OpenAI client: {e}")
    openai_client = None
    MODEL_NAME = None

# --- NEW: A dictionary to map AI tool names to our validation schemas ---
# TOOL_SCHEMA_MAP = {
#     "create_traffic_offence_report": TrafficOffenceReportSchema,
#     "create_investigation_report": InvestigationReportSchema
#     # Add other intents here, e.g.:
#     # "create_witness_statement": WitnessStatementSchema,
# }

class WavAudioCallback(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, audio_buffer: io.BytesIO):
        super().__init__()
        self._buffer = audio_buffer

    def read(self, buffer: memoryview) -> int:
        size = len(buffer)
        data = self._buffer.read(size)
        if not data:
            return 0
        buffer[:len(data)] = data
        return len(data)

    def close(self):
        self._buffer.close()


# --- FastAPI Application Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:5000", "http://0.0.0.0:4200", "http://43.204.127.40", "https://43.204.127.40"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THIS IS THE KEY FIX FOR ACCENTS ---
# We tell Azure to automatically detect the source language from a list of possibilities.
# It will listen for all these English dialects simultaneously.
auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
    languages=["en-US", "en-GB", "en-IN", "en-AU"]
)

def convert_webm_to_wav_bytes(webm_bytes: bytes) -> bytes:
    # ffmpeg_cmd_path = os.getenv("FFMPEG_PATH", "ffmpeg") 
    try:
        input_stream = ffmpeg.input('pipe:0')
        output_stream = ffmpeg.output(
            input_stream.audio,
            'pipe:1',
            format='wav',
            acodec='pcm_s16le',  # 16-bit PCM
            ar='16000',           # 16kHz
            ac='1'                # Mono
        )

        # Run ffmpeg and capture the resulting WAV bytes
        out, _ = ffmpeg.run(output_stream, input=webm_bytes, capture_stdout=True, capture_stderr=True)
        # If you need to override the ffmpeg command location set FFMPEG_PATH in env and use the line below
        # out, _ = ffmpeg.run(output_stream, cmd=ffmpeg_cmd_path, input=webm_bytes, capture_stdout=True, capture_stderr=True)

        return out

    except ffmpeg.Error as e:
        print("An FFmpeg error occurred:", e)
        # It's useful to print stderr to see the actual FFmpeg command line error
        if getattr(e, 'stderr', None):
            try:
                print("FFmpeg stderr:", e.stderr.decode('utf8'))
            except Exception:
                print("FFmpeg stderr (binary):", e.stderr)
        raise  # Re-raise the exception

    except FileNotFoundError:
        # This will now only be raised if the FFMPEG_PATH is wrong or ffmpeg is not in the system PATH
        # print(f"Error: The FFmpeg executable was not found at '{ffmpeg_cmd_path}'.")
        print("Please install FFmpeg and ensure it's in your system's PATH, or set the FFMPEG_PATH environment variable.")
        raise

# --- ENDPOINT 1: Transcribe Audio to Text ---
@app.post("/api/transcribe-audio")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    try:
        audio_data = await audio_file.read()

        # Convert WebM to WAV
        wav_data = convert_webm_to_wav_bytes(audio_data)
        wav_buffer = io.BytesIO(wav_data)
        wav_buffer.seek(0)

        # Prepare audio stream
        callback = WavAudioCallback(wav_buffer)
        stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        pull_stream = speechsdk.audio.PullAudioInputStream(callback, stream_format)
        audio_config = speechsdk.audio.AudioConfig(stream=pull_stream)

        # Speech recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
            audio_config=audio_config
        )

        # 4. Create the phrase list grammar and add our phrases from the file
        phrase_list_grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
        for phrase in PHRASE_LIST:
            phrase_list_grammar.addPhrase(phrase)

        # 5. Continuous Recognition
        full_transcript = []
        done = Event()

        def recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                full_transcript.append(evt.result.text)

        def stop_cb(evt):
            done.set()

        # Attach event handlers
        recognizer.recognized.connect(recognized)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        # Start recognition
        recognizer.start_continuous_recognition()
        done.wait(timeout=60)  # ⏱️ Adjust timeout based on expected audio length
        recognizer.stop_continuous_recognition()

        if full_transcript:
            return {"transcript": " ".join(full_transcript).strip()}
        else:
            raise HTTPException(status_code=400, detail="No speech could be recognized.")

    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
def process_text_with_openai_conversational(text: str, history: List[Message]):
    """
    Acts as an agent: extracts data, checks for missing required fields,
    and asks the user for them in a loop.
    """    
    history = [msg.model_dump() for msg in history]
    # Combine the history and the new message for a full context
    full_context = "\n".join([msg['content'] for msg in history] + [text])
    
    # --- Step 1: Call the AI for pure extraction ---
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": full_context}
    ]

    # 1) Call OpenAI
    response = _run_openai_chat(messages)
    tool_calls = _extract_tool_calls(response)
    if not tool_calls:
        return {"status": "incomplete", "prompt": "Sorry, I couldn't determine the report type. Please be more specific."}

    # 2) Parse the first tool call
    tool_call = tool_calls[0]
    function_name, extracted_data = _parse_tool_call(tool_call)

    if function_name == "unsupported_intent_error":
        return {"status": "error", "intent": "unsupported", "data": extracted_data}

    # 3) Validate schema exists
    validation_schema = TOOL_SCHEMA_MAP.get(function_name)
    if not validation_schema:
        raise HTTPException(status_code=500, detail=f"No validation schema found for tool: {function_name}")

    # 4) Check for missing required fields and ask if necessary
    missing_field_path, question = find_first_missing_field(validation_schema, extracted_data, function_name)
    asked_questions = {msg['content'] for msg in history if msg['role'] == 'assistant'}
    if missing_field_path and question not in asked_questions:
        return {"status": "incomplete", "prompt": question}

    # 5) Post-process and validate final payload
    final_report_json = _postprocess_and_validate(function_name, extracted_data)
    return {"status": "complete", "intent": function_name, "data": final_report_json}


# --- Small helpers used by the processing flows ---
def _run_openai_chat(messages: list):
    """Call the Azure OpenAI chat completions endpoint and return the response object.

    Raises an HTTPException on failure to keep callers simple.
    """
    try:
        return openai_client.chat.completions.create(model=MODEL_NAME, messages=messages, tools=ALL_TOOLS, tool_choice="auto")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {e}")


def _extract_tool_calls(response) -> list:
    """Safely extract any tool calls from a response object."""
    try:
        response_message = response.choices[0].message
        return getattr(response_message, 'tool_calls', []) or []
    except Exception:
        return []


def _parse_tool_call(tool_call) -> tuple[str, dict]:
    """Return (function_name, parsed_args) from a tool_call object; handles JSON errors."""
    function_name = getattr(tool_call.function, 'name', None)
    raw_args = getattr(tool_call.function, 'arguments', '{}')
    try:
        parsed = json.loads(raw_args)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON.")
    return function_name, parsed


def _postprocess_and_validate(function_name: str, args: dict) -> dict:
    """Post-process AI tool args and validate against the mapped Pydantic schema.

    Returns the final validated json-dict or raises HTTPException on failure.
    """
    validation_schema = TOOL_SCHEMA_MAP.get(function_name)
    if not validation_schema:
        raise HTTPException(status_code=500, detail=f"No validation schema found for tool: {function_name}")

    # Choose the correct cleaning function
    if function_name == "create_theft_from_vehicle_report":
        cleaned = process_theft_tool_output(args)
    else:
        cleaned = clean_tool_args(function_name, args)

    # Validate using Pydantic
    try:
        validated = validation_schema.model_validate(cleaned)
        return validated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI output failed validation: {e}")


def process_text_with_openai(text: str, history: List[Message]):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend([msg.dict() for msg in history])
    messages.append({"role": "user", "content": text})

    # 1) Call OpenAI and extract tool calls
    response = _run_openai_chat(messages)
    tool_calls = _extract_tool_calls(response)

    if not tool_calls:
        # Model needs more info or didn't identify intent
        # Use the model's textual content as the prompt if available
        response_message = getattr(response.choices[0], 'message', None)
        content = getattr(response_message, 'content', None) if response_message else None
        return {"status": "incomplete", "prompt": content or "An unexpected error occurred."}

    # 2) Parse first tool call
    tool_call = tool_calls[0]
    function_name, unvalidated_args = _parse_tool_call(tool_call)
    if function_name == "unsupported_intent_error":
        return {"status": "error", "intent": "unsupported", "data": unvalidated_args}

    # 3) Post-process and validate
    final = _postprocess_and_validate(function_name, unvalidated_args)
    return {"status": "complete", "intent": function_name, "data": final}

def find_first_missing_field(schema_model, data: dict, tool_name: str):
    """
    Checks a data dictionary against a Pydantic schema and returns the
    first missing required field and a context-aware, user-friendly question.
    It uses a completely self-contained question map for each tool.
    """
    required_fields = schema_model.model_fields
    
    # Get the specific and complete question map for the current tool.
    # If the tool name is invalid for some reason, default to an empty map.
    specific_questions = QUESTION_MAP.get(tool_name, {})
    
    def get_question(field_name: str, parent_name: str = "") -> tuple[str, str]:
        """Helper to look up the best question and format the final string."""
        
        # Look up the user-friendly name for the parent object (e.g., "the driver")
        parent_subject = specific_questions.get(parent_name, f"the {parent_name.lower()}")
        
        # Look up the user-friendly term for the field itself from the specific map
        question_subject = specific_questions.get(field_name, f"the {field_name.lower()}")
        
        full_path = f"{parent_name}.{field_name}" if parent_name else field_name
        
        if parent_name:
            # Create a context-specific question (e.g., "For the driver, what was the surname?")
            polite_question = f"For {parent_subject}, could you please provide {question_subject}?"
        else:
            polite_question = f"Understood. Could you please provide {question_subject}?"
            
        return full_path, polite_question

    # Iterate through all fields defined in the top-level Pydantic model
    for field_name, field_info in required_fields.items():
        field_data = data.get(field_name)

        # Case 1: The field is a direct, required primitive
        if field_info.is_required() and not field_data:
            return get_question(field_name)

        # Case 2: The field is a nested Pydantic model
        if hasattr(field_info.annotation, 'model_fields'):
            if not field_info.is_required():
                continue

            nested_model = field_info.annotation
            nested_data = field_data if isinstance(field_data, dict) else {}

            for nested_field_name, nested_field_info in nested_model.model_fields.items():
                if nested_field_info.is_required() and not nested_data.get(nested_field_name):
                    # Pass the parent field's name for context
                    return get_question(nested_field_name, parent_name=field_name)

    return None, None # No missing required fields found

@app.post("/api/process-text")
async def process_text(request: TextQueryRequest):
    """Handles a query submitted via keyboard input."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    # The text is already clean, so we can directly call our core OpenAI function.
    return process_text_with_openai(request.text, request.history)


@app.post("/api/process-text-conversational")
async def process_text(request: TextQueryRequest):
    """Handles a query submitted via keyboard input."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    # The text is already clean, so we can directly call our core OpenAI function.
    return process_text_with_openai_conversational(request.text, request.history)


def _parse_relative_date(tok: str, today: date) -> str:
    t = tok.strip().lower()
    if t == "today": return today.strftime("%d/%m/%Y")
    if t == "yesterday": return (today - timedelta(days=1)).strftime("%d/%m/%Y")
    if t == "tomorrow": return (today + timedelta(days=1)).strftime("%d/%m/%Y")
    # common phrases
    if re.search(r"\blast night\b|\bthis morning\b|\bthis afternoon\b", t):
        # map to yesterday or today conservatively
        return today.strftime("%d/%m/%Y") if "this" in t else (today - timedelta(days=1)).strftime("%d/%m/%Y")
    return tok  # leave unchanged if unknown

def normalise_date_field(value: str) -> str:
    if not value: return ""
    today = datetime.utcnow().date()  # use server timezone if required
    v = value.strip()
    return _parse_relative_date(v, today) if v.lower() in {"today","yesterday","tomorrow"} or re.search(r"\b(today|yesterday|tomorrow|this morning|last night)\b", v.lower()) else v


def normalize_time(value: str) -> str:
    """Normalize time strings to HH:MM when possible.

    - Returns empty string for falsy input
    - If an explicit HH:MM-like pattern exists, returns that
    - Otherwise attempts to parse using dateparser and formats as HH:MM
    - Falls back to trimmed original value when parsing fails
    """
    if not value:
        return ""
    v = str(value).strip()

    # Quick match for explicit hh:mm or h:mm patterns
    m = re.search(r"(\d{1,2}:\d{2})", v)
    if m:
        return m.group(1)

    # Try to parse fuzzy time expressions like '3pm', 'half past 2', 'around 14:30'
    try:
        parsed = dateparser.parse(v)
        if isinstance(parsed, datetime):
            return parsed.strftime("%H:%M")
    except Exception:
        pass

    # Fallback to returning the trimmed original
    return v

def process_theft_tool_output(tool_result: dict) -> dict:
    """Clean the AI output for the theft-from-vehicle tool to match the schema shape.
    """

    def cap(v: any) -> str:
        return v.strip().capitalize() if isinstance(v, str) and v.strip() else ""

    raw = tool_result if isinstance(tool_result, dict) else {}

    event_location = raw.get("EventLocation") if isinstance(raw.get("EventLocation"), dict) else {}
    vehicle = raw.get("Vehicle") if isinstance(raw.get("Vehicle"), dict) else {}
    victim = raw.get("Victim") if isinstance(raw.get("Victim"), dict) else {}
    victim_address = victim.get("Address") if isinstance(victim.get("Address"), dict) else {}

    cleaned = {
        "Classification": cap(raw.get("Classification", "")),
        "EventDate": normalise_date_field(raw.get("EventDate", "")),
        "EventTime": normalize_time(raw.get("EventTime", "")),

        "EventLocation": {
            "PremisesName": event_location.get("PremisesName", ""),
            "PremisesNumber": event_location.get("PremisesNumber", ""),
            "StreetName": event_location.get("StreetName", ""),
            "TownOrCity": event_location.get("TownOrCity", "")
        },

        "Vehicle": {
            "VehicleRegistrationMark": validate_vrm(vehicle.get("VehicleRegistrationMark", "")),
            "Make": cap(vehicle.get("Make", "")),
            "Model": cap(vehicle.get("Model", "")),
            "Colour": cap(vehicle.get("Colour", ""))
        },

        "Victim": {
            "Surname": cap(victim.get("Surname", "")),
            "Forename1": cap(victim.get("Forename1", "")),
            "Forename2": cap(victim.get("Forename2", "")),
            "DateOfBirth": normalise_date_field(victim.get("DateOfBirth", "")),
            "Sex": cap(victim.get("Sex", "")),
            "Address": {
                "PremisesName": victim_address.get("PremisesName", ""),
                "PremisesNumber": victim_address.get("PremisesNumber", ""),
                "StreetName": victim_address.get("StreetName", ""),
                "TownOrCity": victim_address.get("TownOrCity", "")
            }
        },

        "VehicleDamage": raw.get("VehicleDamage", ""),
        "CCTVAvailable": bool(raw.get("CCTVAvailable", False)),
        "CCTVLocation": raw.get("CCTVLocation", ""),
        "StolenItems": raw.get("StolenItems") if isinstance(raw.get("StolenItems"), list) else ( [raw.get("StolenItems")] if raw.get("StolenItems") else [] )
    }

    # Ensure we don't accidentally copy victim address into event location when event location is blank
    if not any(cleaned["EventLocation"].values()):
        # leave explicit empty strings (do not populate from victim address)
        cleaned["EventLocation"] = {"PremisesName":"", "PremisesNumber":"", "StreetName":"", "TownOrCity":""}

    # Classification fallback if still empty
    if not cleaned["Classification"]:
        if cleaned["StolenItems"]:
            cleaned["Classification"] = "Theft From Motor Vehicle"
        else:
            damage = cleaned.get("VehicleDamage", "") or ""
            if damage and re.search(r'\b(window|lock|tamper|smashed|forced|damage)\b', damage, re.I):
                cleaned["Classification"] = "Vehicle Interference"
            else:
                cleaned["Classification"] = "Vehicle Interference"

    return cleaned

def validate_vrm(value: str) -> str:
    # Normalize spacing and case
    value = re.sub(r"\s+", "", value.upper().strip())
    
    #Commented purposely
    # Validate against the modern UK VRM format (since 2001): AAnnAAA
    # if re.match(r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$", value):
    #     # Format it nicely with a space for readability: e.g., "SJ22HKL" → "SJ22 HKL"
    #     return value[:4] + " " + value[4:]    
    # return ""

    return value

def clean_tool_args(tool_name: str, args: dict) -> dict:
    """
    Safely accesses nested dictionaries from the AI's output,
    normalizes the values (dates, times, etc.), and rebuilds the
    structure to perfectly match the Pydantic schemas.
    """
    
    # Helper for safe capitalization
    def capitalize_safely(value: any) -> str:
        return value.strip().capitalize() if isinstance(value, str) else ""

    # This function is now the single source of truth for post-processing.
    if tool_name == "create_traffic_offence_report":
        # Step 1: Safely get the nested objects from the AI's raw output.
        location_data = args.get("OffenceLocation") if isinstance(args.get("OffenceLocation"), dict) else {}
        driver_data = args.get("Driver") if isinstance(args.get("Driver"), dict) else {}
        vehicle_data = args.get("Vehicle") if isinstance(args.get("Vehicle"), dict) else {}
        
        # Check for the deeply nested address as well.
        driver_address_data = driver_data.get("Address") if isinstance(driver_data.get("Address"), dict) else {}
        
        # Step 2: Build a new, clean dictionary with the correct structure.
        cleaned_args = {
            "OffenceDate": normalise_date_field(args.get("OffenceDate", "")),
            "OffenceTime": normalize_time(args.get("OffenceTime", "")),
            "Offence": capitalize_safely(args.get("Offence", "")),            
            "OffenceLocation": {
                # Operate on the correct sub-dictionary
                "StreetName": location_data.get("StreetName", ""),
                "TownOrCity": location_data.get("TownOrCity", "")
            },            
            "Driver": {
                "Surname": capitalize_safely(driver_data.get("Surname", "")),
                "Forename1": capitalize_safely(driver_data.get("Forename1", "")),
                "Forename2": capitalize_safely(driver_data.get("Forename2", "")),
                "DateOfBirth": normalise_date_field(driver_data.get("DateOfBirth", "")),
                "Sex": capitalize_safely(driver_data.get("Sex", "")),
                
                "Address": {
                    "PremisesName": driver_address_data.get("PremisesName", ""),
                    "PremisesNumber": driver_address_data.get("PremisesNumber", ""),
                    "StreetName": driver_address_data.get("StreetName", ""),
                    "TownOrCity": driver_address_data.get("TownOrCity", "")
                }
            },
            "Vehicle": {
                "VehicleRegistrationMark": validate_vrm(vehicle_data.get("VehicleRegistrationMark", "")),
                "Make": capitalize_safely(vehicle_data.get("Make", "")),
                "Model": capitalize_safely(vehicle_data.get("Model", "")),
                "Colour": capitalize_safely(vehicle_data.get("Colour", ""))
            }
        }
        return cleaned_args

    elif tool_name == "create_investigation_report":
        # Apply the same robust, nested logic for the investigation report
        location_data = args.get("EventLocation") if isinstance(args.get("EventLocation"), dict) else {}
        victim_data = args.get("Victim") if isinstance(args.get("Victim"), dict) else {}
        victim_address_data = victim_data.get("Address") if isinstance(victim_data.get("Address"), dict) else {}
        stolen_vehicle_data = args.get("StolenVehicle") if isinstance(args.get("StolenVehicle"), dict) else None
        suspect_vehicle_data = args.get("SuspectVehicle") if isinstance(args.get("SuspectVehicle"), dict) else None
        
        cleaned_args = {
            "Classification": capitalize_safely(args.get("Classification", "")),
            "EventDate": normalise_date_field(args.get("EventDate", "")),
            "EventTime": normalize_time(args.get("EventTime", "")),
            
            "EventLocation": {
                "PremisesName": location_data.get("PremisesName", ""),
                "PremisesNumber": location_data.get("PremisesNumber", ""),
                "StreetName": location_data.get("StreetName", ""),
                "TownOrCity": location_data.get("TownOrCity", "")
            },
            
            "Victim": {
                "Surname": capitalize_safely(victim_data.get("Surname", "")),
                "Forename1": capitalize_safely(victim_data.get("Forename1", "")),
                "Forename2": capitalize_safely(victim_data.get("Forename2", "")),
                "DateOfBirth": normalise_date_field(victim_data.get("DateOfBirth", "")),
                "Sex": capitalize_safely(victim_data.get("Sex", "")),
                
                "Address": {
                    "PremisesName": victim_address_data.get("PremisesName", ""),
                    "PremisesNumber": victim_address_data.get("PremisesNumber", ""),
                    "StreetName": victim_address_data.get("StreetName", ""),
                    "TownOrCity": victim_address_data.get("TownOrCity", "")
                }
            }
        }
        
        if stolen_vehicle_data:
            cleaned_args["StolenVehicle"] = {
                "VehicleRegistrationMark": validate_vrm(stolen_vehicle_data.get("VehicleRegistrationMark", "")),
                "Make": capitalize_safely(stolen_vehicle_data.get("Make", "")),
                "Model": capitalize_safely(stolen_vehicle_data.get("Model", "")),
                "Colour": capitalize_safely(stolen_vehicle_data.get("Colour", ""))
            }
        
        if suspect_vehicle_data:
            cleaned_args["SuspectVehicle"] = {
                "VehicleRegistrationMark": validate_vrm(suspect_vehicle_data.get("VehicleRegistrationMark", "")),
                "Make": capitalize_safely(suspect_vehicle_data.get("Make", "")),
                "Model": capitalize_safely(suspect_vehicle_data.get("Model", "")),
                "Colour": capitalize_safely(suspect_vehicle_data.get("Colour", ""))
            }
            
        return cleaned_args

    # Fallback to return the original arguments if the tool name doesn't match
    return args

@app.get("/")
def read_root():
    return {"status": "Officer Insights Multi-Intent API is running"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Convert HTTPExceptions (including those raised with Azure/OpenAI error payloads)
    into a simple, friendly JSON response.
    """
    detail = exc.detail
    # Normalize to text for simple inspection
    if isinstance(detail, (dict, list)):
        detail_text = json.dumps(detail)
    else:
        detail_text = str(detail or "")

    # Detect Azure/OpenAI content filter markers
    if "content_filter" in detail_text or "ResponsibleAIPolicyViolation" in detail_text or "content_filter_result" in detail_text:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": "content_filtered",
                "message": "Error occurred from Azure OpenAI. The response was filtered due to the prompt triggering Azure OpenAI's content management policy. We could not process that input because it contains restricted content. Please remove or rephrase restricted or graphic details and try again."
            },
        )

    # Generic friendly HTTP error response
    friendly_message = detail_text if detail_text else "An error occurred processing your request."
    return JSONResponse(
        status_code=exc.status_code if getattr(exc, "status_code", None) else 500,
        content={
            "status": "error",
            "error": "http_error",
            "message": friendly_message
        },
    )