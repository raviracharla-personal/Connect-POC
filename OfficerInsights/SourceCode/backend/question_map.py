# This file contains a centralized and context-aware mapping of technical
# field names to user-friendly, polite questions, categorized by report type.
# Each report type has its own complete, self-contained dictionary.

QUESTION_MAP = {
    "create_traffic_offence_report": {
        # Top-level fields
        "OffenceDate": "the date of the offence",
        "OffenceTime": "the time of the offence",
        "Offence": "the specific offence committed",
        
        # Parent Objects
        "OffenceLocation": "the location of the offence",
        "Driver": "the driver",
        "Vehicle": "the vehicle",
        "Address": "the driver's address",

        # Nested Person/Driver fields
        "Surname": "the driver's surname",
        "Forename1": "the driver's first name",
        "Forename2": "the driver's middle name",
        "DateOfBirth": "the driver's date of birth",
        "Sex": "the driver's sex (Male or Female)",
        
        # Nested Vehicle fields
        "VehicleRegistrationMark": "the vehicle's registration mark (VRM)",
        "Make": "the make of the vehicle",
        "Model": "the model of the vehicle",
        "Colour": "the colour of the vehicle",

        # Nested Address/Location fields
        "StreetName": "the street name",
        "TownOrCity": "the town or city",
        "PremisesNumber": "the premises number (house or building number)",
        "PremisesName": "the premises name (e.g., building name)"
    },
    
    "create_investigation_report": {
        # Top-level fields
        "Classification": "the classification of the incident (e.g., Theft, Burglary)",
        "EventDate": "the date of the event",
        "EventTime": "the time of the event",

        # Parent Objects
        "EventLocation": "the location of the event",
        "Victim": "the victim",
        "StolenVehicle": "the stolen vehicle",
        "SuspectVehicle": "the suspect vehicle",
        "Address": "the victim's address",

        # Nested Person/Victim fields
        "Surname": "the victim's surname",
        "Forename1": "the victim's first name",
        "DateOfBirth": "the victim's date of birth",
        "Sex": "the victim's sex (Male or Female)",
        
        # Nested Vehicle fields (can apply to Stolen or Suspect)
        "VehicleRegistrationMark": "the vehicle's registration mark (VRM)",
        "Make": "the make of the vehicle",
        "Model": "the model of the vehicle",
        "Colour": "the colour of the vehicle",

        # Nested Address/Location fields
        "StreetName": "the street name",
        "TownOrCity": "the town or city",
        "PremisesNumber": "the premises number (house or building number)",
        "PremisesName": "the premises name (e.g., building or business name)"
    },
    "create_theft_from_vehicle_report": {
        # Top-level fields
        "Classification": "the offence classification (Theft From Motor Vehicle or Vehicle Interference)",
        "EventDate": "the date when the incident occurred",
        "EventTime": "the time when the incident occurred",

        # Parent Objects
        "EventLocation": "the location where the vehicle was when the incident occurred",
        "Vehicle": "the vehicle involved",
        "Victim": "the victim / vehicle owner",
        "Address": "the victim's residential address",

        # Vehicle fields
        "VehicleRegistrationMark": "the vehicle's registration mark (VRM)",
        "Make": "the make of the vehicle",
        "Model": "the model of the vehicle",
        "Colour": "the colour of the vehicle",

        # Victim fields
        "Surname": "the victim's surname",
        "Forename1": "the victim's first name",
        "Forename2": "the victim's middle name (if any)",
        "DateOfBirth": "the victim's date of birth",
        "Sex": "the victim's sex (Male or Female)",

        # Damage / CCTV / property fields
        "VehicleDamage": "a description of any damage to the vehicle",
        "CCTVAvailable": "whether CCTV is available (Yes or No)",
        "CCTVLocation": "where the CCTV or security footage can be accessed",
        "PropertyTaken": "whether the victim knows what property has been taken (Yes or No)",
        "StolenItems": "what property has been taken from the vehicle (list the items)",

        # Address/Location fields
        "StreetName": "the street name",
        "TownOrCity": "the town or city",
        "PremisesNumber": "the premises number (house or building number)",
        "PremisesName": "the premises name (e.g., building or business name)"
    }
}