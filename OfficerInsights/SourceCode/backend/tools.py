# This file defines the "tools" (structured data schemas) that our AI can use.
# Each tool corresponds to a specific police reporting intent.

from openai.types.shared_params import FunctionDefinition
from schemas import InvestigationReportSchema

# In backend/tools.py
from typing import Type
from pydantic import BaseModel
from schemas import TrafficOffenceReportSchema, InvestigationReportSchema, TheftFromMotorVehicleSchema

def pydantic_to_openai_tool(
    model: Type[BaseModel], 
    tool_name: str, 
    tool_description: str
) -> dict:
    """
    Converts a Pydantic model into a JSON schema compatible with OpenAI's 'function' tool type.
    """
    # Get the JSON schema from the Pydantic model
    schema = model.model_json_schema()

    # The OpenAI tool format requires a 'function' wrapper
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        },
    }

# --- Automatically generate the tools from our Pydantic schemas ---

traffic_offence_tool = pydantic_to_openai_tool(
    model=TrafficOffenceReportSchema,
    tool_name="create_traffic_offence_report",
    tool_description="Extract structured offence details from unstructured text reported by an officer for a traffic offence. Use this for violations like speeding, no seatbelt, etc."
)

investigation_report_tool = pydantic_to_openai_tool(
    model=InvestigationReportSchema,
    tool_name="create_investigation_report",
    tool_description="Extract structured investigation event details from free-text reported by an officer, including location, victim, and any vehicle involvement."
)

theft_from_vehicle_tool = pydantic_to_openai_tool(
    model=TheftFromMotorVehicleSchema,
    tool_name="create_theft_from_vehicle_report",
    tool_description="Extract structured details about a theft from motor vehicle incident. Use this when items have been stolen from a vehicle or when there's evidence of attempted theft/interference with a vehicle."
)

unsupported_intent_tool = {
    "type": "function",
    "function": {
        "name": "unsupported_intent_error",
        "description": "Call this tool when the user's query is not a valid traffic offence or investigation report. Use this for general questions, unsupported commands, or ambiguous input.",
        "parameters": {
            "type": "object",
            "properties": {
                "errorMessage": {
                    "type": "string",
                    "description": "A brief, user-facing explanation of why the request could not be processed. Example: 'The request is not a valid traffic offence or investigation report.'"
                },
                "originalQuery": {
                    "type": "string",
                    "description": "The full, verbatim query from the user."
                }
            },
            "required": ["errorMessage", "originalQuery"]
        }
    }
}

# A single list containing all our auto-generated tools
ALL_TOOLS = [
    traffic_offence_tool, 
    investigation_report_tool, 
    theft_from_vehicle_tool,
    unsupported_intent_tool
]


# # --- Tool 1: Traffic Offence Report ---
# traffic_offence_tool = {
#     "type": "function",
#     "function": {
#         "name": "create_traffic_offence_report",
#         "description": "Extract structured offence details from unstructured text reported by an officer for a traffic offence. Use this for violations like speeding, no seatbelt, red light jumping, mobile phone use while driving, etc.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "OffenceLocation": {
#                     "type": "object",
#                     "description": "Location where the traffic offence occurred.",
#                     "properties": {
#                         "StreetName": {
#                             "type": "string",
#                             "description": "Street or road name where the offence happened, including direction if applicable (e.g., 'M4 Eastbound', 'High Street')."
#                         },
#                         "TownOrCity": {
#                             "type": "string",
#                             "description": "The town or city where the offence took place (not a landmark)."
#                         }
#                     },
#                     "required": ["StreetName", "TownOrCity"]
#                 },
#                 "Driver": {
#                     "type": "object",
#                     "description": "Details about the driver involved in the traffic offence.",
#                     "properties": {
#                         "Forename1": {
#                             "type": "string",
#                             "description": "Driver's first name as recorded on official documents."
#                         },
#                         "Forename2": {
#                             "type": "string",
#                             "description": "Driver's middle name, if available."
#                         },
#                         "Surname": {
#                             "type": "string",
#                             "description": "Driver's last name or family name."
#                         },
#                         "DateOfBirth": {
#                             "type": "string",
#                             "description": "Driver's date of birth in DD/MM/YYYY format. Use an empty string if not provided."
#                         },
#                         "Sex": {
#                             "type": "string",
#                             "enum": ["Male", "Female", ""],
#                             "description": "Driver's gender identity. Use 'Male', 'Female', or empty string if unknown."
#                         },
#                         "Address": {
#                             "type": "object",
#                             "description": "The address where the driver resides.",
#                             "properties": {
#                                 "PremisesName": {
#                                     "type": "string",
#                                     "description": "Name of the premises (e.g., building name or flat name)."
#                                 },
#                                 "PremisesNumber": {
#                                     "type": "string",
#                                     "description": "House or flat number at the address."
#                                 },
#                                 "StreetName": {
#                                     "type": "string",
#                                     "description": "Street name of the driver's address."
#                                 },
#                                 "TownOrCity": {
#                                     "type": "string",
#                                     "description": "Town or city of the driver's address."
#                                 }
#                             },
#                             "required": ["PremisesName", "PremisesNumber", "StreetName", "TownOrCity"]
#                         }
#                     },
#                     "required": ["Forename1", "Surname", "DateOfBirth", "Sex", "Address"]
#                 },
#                 "Vehicle": {
#                     "type": "object",
#                     "description": "Information about the vehicle involved in the offence.",
#                     "properties": {
#                         "VehicleRegistrationMark": {
#                             "type": "string",
#                             "description": "The full UK vehicle registration number, in uppercase (e.g., 'MT21 FJU')."
#                         },
#                         "Make": {
#                             "type": "string",
#                             "description": "Brand or manufacturer of the vehicle (e.g., 'Ford', 'BMW')."
#                         },
#                         "Model": {
#                             "type": "string",
#                             "description": "Model of the vehicle (e.g., 'Focus', 'Transit')."
#                         },
#                         "Colour": {
#                             "type": "string",
#                             "description": "Exterior colour of the vehicle (e.g., 'Red', 'Black')."
#                         }
#                     },
#                     "required": ["VehicleRegistrationMark", "Make", "Model", "Colour"]
#                 },
#                 "OffenceDate": {
#                     "type": "string",
#                     "description": "The date when the offence occurred in DD/MM/YYYY format. If the text says 'today' or 'yesterday', retain it as-is."
#                 },
#                 "OffenceTime": {
#                     "type": "string",
#                     "description": "The time of the offence in 24-hour HH:MM format (e.g., '08:45', '14:30')."
#                 },
#                 "Offence": {
#                     "type": "string",
#                     "description": "The specific nature of the traffic offence (e.g., 'No Seat Belt', 'Speeding in a 30 mph zone')."
#                 }
#             },
#             "required": [
#                 "OffenceLocation",
#                 "Driver",
#                 "Vehicle",
#                 "OffenceDate",
#                 "OffenceTime",
#                 "Offence"
#             ]
#         }
#     }
# }


# create_investigation_report_tool = {
#     "type": "function",
#     "function": {
#         "name": "create_investigation_report",
#         "description": "Extract structured investigation event details from free-text reported by a police officer. Use for incidents like theft, assault, burglary, and related vehicle involvement.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "Classification": {
#                     "type": "string",
#                     "description": "Type or classification of the incident, such as 'Theft', 'Assault', 'Burglary', or 'Criminal Damage'."
#                 },
#                 "EventDate": {
#                     "type": "string",
#                     "description": "The date the event occurred. Use DD/MM/YYYY format. If the text says 'today' or 'yesterday', output exactly 'today' or 'yesterday'."
#                 },
#                 "EventTime": {
#                     "type": "string",
#                     "description": "The time the event occurred in 24-hour HH:MM format (e.g., '14:30')."
#                 },
#                 "EventLocation": {
#                     "type": "object",
#                     "description": "The location where the investigation incident occurred.",
#                     "properties": {
#                         "PremisesName": {
#                             "type": "string",
#                             "description": "The name of the building, shop, or business involved in the incident (e.g., 'Tesco Express', 'St. Mary's Flat')."
#                         },
#                         "PremisesNumber": {
#                             "type": "string",
#                             "description": "House or flat number at the location of the incident (e.g., '24B')."
#                         },
#                         "StreetName": {
#                             "type": "string",
#                             "description": "Name of the street where the event occurred."
#                         },
#                         "TownOrCity": {
#                             "type": "string",
#                             "description": "Town or city where the event took place (not a landmark)."
#                         }
#                     },
#                     "required": ["StreetName", "TownOrCity"]
#                 },
#                 "Victim": {
#                     "type": "object",
#                     "description": "Information about the victim involved in the investigation.",
#                     "properties": {
#                         "Surname": {
#                             "type": "string",
#                             "description": "Victim's last name or family name."
#                         },
#                         "Forename1": {
#                             "type": "string",
#                             "description": "Victim's first name as recorded."
#                         },
#                         "Forename2": {
#                             "type": "string",
#                             "description": "Victim's middle name, if available."
#                         },
#                         "DateOfBirth": {
#                             "type": "string",
#                             "description": "Victim's date of birth in DD/MM/YYYY format. Use empty string ('') if unknown or not mentioned."
#                         },
#                         "Sex": {
#                             "type": "string",
#                             "enum": ["Male", "Female", ""],
#                             "description": "Victim's sex as 'Male', 'Female', or empty string if unspecified."
#                         },
#                         "Address": {
#                             "type": "object",
#                             "description": "Address of the victim's residence.",
#                             "properties": {
#                                 "PremisesName": {
#                                     "type": "string",
#                                     "description": "Building name or flat name of victim's address, e.g., 'Maple House'."
#                                 },
#                                 "PremisesNumber": {
#                                     "type": "string",
#                                     "description": "Flat or house number at the address."
#                                 },
#                                 "StreetName": {
#                                     "type": "string",
#                                     "description": "Street name where the victim resides."
#                                 },
#                                 "TownOrCity": {
#                                     "type": "string",
#                                     "description": "Town or city of the victim's residence."
#                                 }
#                             },
#                             "required": ["StreetName", "TownOrCity"]
#                         }
#                     },
#                     "required": ["Surname", "Forename1", "DateOfBirth", "Sex", "Address"]
#                 },
#                 "StolenVehicle": {
#                     "type": "object",
#                     "description": "If a vehicle was stolen, provide details here.",
#                     "properties": {
#                         "VehicleRegistrationMark": {
#                             "type": "string",
#                             "description": "UK-style license plate number of the stolen vehicle, e.g., 'MT21 FJU'."
#                         },
#                         "Make": {
#                             "type": "string",
#                             "description": "Manufacturer of the stolen vehicle, e.g., 'Ford'."
#                         },
#                         "Model": {
#                             "type": "string",
#                             "description": "Model of the stolen vehicle, e.g., 'Focus'."
#                         },
#                         "Colour": {
#                             "type": "string",
#                             "description": "Colour of the stolen vehicle, e.g., 'Black'."
#                         }
#                     }
#                 },
#                 "SuspectVehicle": {
#                     "type": "object",
#                     "description": "If a suspect was seen in a vehicle, describe it here.",
#                     "properties": {
#                         "VehicleRegistrationMark": {
#                             "type": "string",
#                             "description": "UK-style license plate number of the suspect vehicle, e.g., 'AB12 XYZ'."
#                         },
#                         "Make": {
#                             "type": "string",
#                             "description": "Manufacturer of the suspect vehicle."
#                         },
#                         "Model": {
#                             "type": "string",
#                             "description": "Model of the suspect vehicle."
#                         },
#                         "Colour": {
#                             "type": "string",
#                             "description": "Colour of the suspect vehicle."
#                         }
#                     }
#                 }
#             },
#             "required": [
#                 "Classification",
#                 "EventDate",
#                 "EventTime",
#                 "EventLocation",
#                 "Victim"
#             ]
#         }
#     }
# }


# # --- Tool 2: Witness Statement ---
# witness_statement_tool = {
#     "type": "function",
#     "function": {
#         "name": "create_witness_statement",
#         "description": "Records a witness's account of an incident. Use this when an officer is taking a statement from someone who saw an event.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "IncidentReference": {"type": "string", "description": "The police incident reference number, if known."},
#                 "StatementDateTime": {"type": "string", "description": "The date and time the statement is being taken, in ISO 8601 format (e.g., 2024-05-26T15:30:00Z). Infer from context like 'now' or 'today at 3:30 pm'."},
#                 "IncidentLocation": {
#                     "type": "object",
#                     "properties": { "PremisesName": {"type": "string"}, "StreetName": {"type": "string"}, "TownOrCity": {"type": "string"} },
#                     "required": ["StreetName", "TownOrCity"]
#                 },
#                 "Witness": {
#                     "type": "object",
#                     "properties": { "Forename1": {"type": "string"}, "Surname": {"type": "string"}, "ContactNumber": {"type": "string"} },
#                     "required": ["Forename1", "Surname", "ContactNumber"]
#                 },
#                 "StatementText": {"type": "string", "description": "The witness's verbatim account of what they saw or heard."}
#             },
#             "required": ["StatementDateTime", "IncidentLocation", "Witness", "StatementText"]
#         }
#     }
# }

# # --- Tool 3: Stolen Vehicle Report ---
# stolen_vehicle_tool = {
#     "type": "function",
#     "function": {
#         "name": "create_stolen_vehicle_report",
#         "description": "Logs a report for a vehicle that has been stolen. Use this when the primary event is vehicle theft.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "TheftDate": {"type": "string", "description": "The approximate date the vehicle was stolen. Infer from 'last night' or 'yesterday'."},
#                 "TheftTime": {"type": "string", "description": "The approximate time the vehicle was stolen."},
#                 "LastSeenLocation": {
#                     "type": "object",
#                     "properties": { "PremisesNumber": {"type": "string"}, "StreetName": {"type": "string"}, "TownOrCity": {"type": "string"} },
#                     "required": ["StreetName", "TownOrCity"]
#                 },
#                 "Owner": {"type": "object", "properties": {"FullName": {"type": "string"}}, "required": ["FullName"]},
#                 "Vehicle": {
#                     "type": "object",
#                     "properties": { "VehicleRegistrationMark": {"type": "string"}, "Make": {"type": "string"}, "Model": {"type": "string"}, "Colour": {"type": "string"} },
#                     "required": ["VehicleRegistrationMark", "Make", "Model", "Colour"]
#                 }
#             },
#             "required": ["TheftDate", "LastSeenLocation", "Owner", "Vehicle"]
#         }
#     }
# }

# # --- Tool 4: Stop and Search Record ---
# stop_and_search_tool = {
#     "type": "function",
#     "function": {
#         "name": "create_stop_and_search_record",
#         "description": "Creates a formal record of a stop and search encounter. This is a legally significant record.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "StopDateTime": {"type": "string", "description": "The date and time of the stop and search, in ISO 8601 format."},
#                 "StopLocation": {
#                     "type": "object",
#                     "properties": { "LocationName": {"type": "string", "description": "A specific name for the location, e.g., 'Piccadilly Gardens' or 'outside the station'."}, "TownOrCity": {"type": "string"} },
#                     "required": ["LocationName", "TownOrCity"]
#                 },
#                 "Subject": {
#                     "type": "object",
#                     "properties": {
#                         "Description": {"type": "string", "description": "A physical description of the person, e.g., 'white male, approx 25, slim build, wearing a black tracksuit'."},
#                         "Name": {"type": "string", "description": "The subject's full name, if obtained."},
#                         "Gender": {"type": "string", "enum": ["Male", "Female", "Unknown"]}
#                     },
#                     "required": ["Description"]
#                 },
#                 "GroundsForSearch": {
#                     "type": "object",
#                     "properties": {
#                         "Legislation": {"type": "string", "description": "The legal power used, e.g., 'Section 23 Misuse of Drugs Act'."},
#                         "Reason": {"type": "string", "description": "The specific reason for the search, e.g., 'Smelling of cannabis'."}
#                     },
#                     "required": ["Legislation", "Reason"]
#                 },
#                 "Outcome": {"type": "string", "description": "The result of the search, e.g., 'Nothing Found', 'Cannabis Found - Community Resolution'."}
#             },
#             "required": ["StopDateTime", "StopLocation", "Subject", "GroundsForSearch", "Outcome"]
#         }
#     }
# }

# # --- A list containing all available tools ---
# ALL_TOOLS = [
#     traffic_offence_tool,
#     create_investigation_report_tool,
#     witness_statement_tool,
#     stolen_vehicle_tool,
#     stop_and_search_tool
# ]

# Update the TOOL_SCHEMA_MAP
TOOL_SCHEMA_MAP = {
    "create_traffic_offence_report": TrafficOffenceReportSchema,
    "create_investigation_report": InvestigationReportSchema,
    "create_theft_from_vehicle_report": TheftFromMotorVehicleSchema
}