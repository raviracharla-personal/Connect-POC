# This file contains a centralized list of domain-specific words, acronyms,
# and phrases to improve the accuracy of the speech-to-text transcription.

# By adding "TOR", we tell the service to prefer it over the homophone "tour".
# Add any other jargon, street names, or common terms that are
# transcribed incorrectly.

POLICE_ACRONYMS = [
    "TOR", "MISPER", "PNC", "RTS", "RTC", "RTA", "ANPR", "APNR", "CRIS", "CAD",
    "MG11", "MG5", "MG6", "DVLA", "CCTV", "ASB"
]

POLICE_OFFENCES = [
    "Traffic offence",
    "Dangerous driving",
    "Drink driving",
    "Driving under the influence",
    "Driving without insurance",
    "No insurance",
    "No seatbelt",
    "Speeding in a 30",
    "Excess speed",
    "Red light offence",
    "Driving without a license",
    "Use of mobile phone while driving",
    "Vehicle seized",
    "Unroadworthy vehicle",
    "Failing to stop",
    "Fail to provide",
    "Public order offence",
    "Theft from motor vehicle",
    "Non dwelling burglary",
    "Breach of peace"
]

INVESTIGATION_PHRASES = [
    "Victim details",
    "Suspect description",
    "Stolen vehicle",
    "Suspect vehicle",
    "House to house enquiries",
    "Scene of crime",
    "Crime scene",
    "Statement taken",
    "Witness present",
    "Evidence collected",
    "Investigation ongoing",
    "Perpetrator",
    "Male offender",
    "Female suspect",
    "Classification",
    "Premises name",
    "Date of birth",
    "Residential address"
]


VEHICLE_TERMS = [
    "VRM",
    "Vehicle registration mark",
    "Reg plate",
    "Ford Transit",
    "Ford Fiesta",
    "Audi A4",
    "Black Audi",
    "Red Ford",
    "Make and model",
    "Registration plate",
    "Unmarked car",
    "Marked vehicle",
    "Dash cam footage",
    "Body cam footage"
]


LOCATION_TERMS = [
    "Custody suite",
    "Station van",
    "Blue lights",
    "Pursuit initiated",
    "Dispatch received",
    "Patrol car",
    "Control room",
    "Traffic stop",
    "Road traffic stop",
    "A6 Stockport",
    "Appleby Court",
    "Rosewood Close",
    "Rosewood House"
]


OFFICER_TERMS = [
    "Bobby",
    "Sarge",
    "Sergeant",
    "Detective",
    "PC",
    "DS",
    "DI",
    "Inspector",
    "CID",
    "Blues and twos"
]


COMMON_MISHEARD = [
    "Tour",   # Instead of "TOR"
    "Appellate court",  # Instead of "Appleby Court"
    "Rose would close", # Instead of "Rosewood Close"
    "Mt twenty one f j u",  # Instead of "MT21 FJU"
    "A and P R",         # Instead of "ANPR"
    "Mister", "Misses", "DOB", "VRM"
]


PHRASE_LIST = (
    POLICE_ACRONYMS +
    POLICE_OFFENCES +
    INVESTIGATION_PHRASES +
    VEHICLE_TERMS +
    LOCATION_TERMS +
    OFFICER_TERMS +
    COMMON_MISHEARD
)
