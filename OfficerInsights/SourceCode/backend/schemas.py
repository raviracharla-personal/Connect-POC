# In backend/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

# This file is now the single source of truth for all data structures.

class AddressSchema(BaseModel):
    PremisesName: Optional[str] = Field(default="", description="Name of the premises (e.g., building or flat name).")
    PremisesNumber: Optional[str] = Field(default="", description="House or flat number at the address.")
    StreetName: str = Field(description="Street name of the address.")
    TownOrCity: str = Field(description="Town or city of the address.")

class PersonSchema(BaseModel):
    Surname: str = Field(description="Person's last name or family name.")
    Forename1: str = Field(description="Person's first name.")
    Forename2: Optional[str] = Field(default="", description="Person's middle name, if available.")
    DateOfBirth: str = Field(description="Person's date of birth in DD/MM/YYYY format.")
    Sex: Optional[str] = Field(
        default="",
        description="Person's gender ('Male' or 'Female'). Optional field."
    )
    Address: AddressSchema = Field(description="The person's residential address.")

class VehicleSchema(BaseModel):
    VehicleRegistrationMark: str = Field(description="The full UK vehicle registration mark (VRM), in uppercase.")
    Make: str = Field(description="Brand or manufacturer of the vehicle (e.g., 'Ford').")
    Model: str = Field(description="Model of the vehicle (e.g., 'Focus').")
    Colour: str = Field(description="Exterior colour of the vehicle.")

class TrafficOffenceReportSchema(BaseModel):
    OffenceDate: str = Field(description="The date when the offence occurred in DD/MM/YYYY format. If the text says 'today' or 'yesterday', retain it as-is.")
    OffenceTime: str = Field(description="The time of the offence in 24-hour HH:MM format (e.g., '08:45', '14:30').")
    Offence: str = Field(description="The specific nature of the traffic offence (e.g., 'No Seat Belt', 'Speeding in a 30 mph zone').")
    OffenceLocation: AddressSchema = Field(description="Location where the traffic offence occurred.")
    Driver: PersonSchema = Field(description="Details about the driver involved.")
    Vehicle: VehicleSchema = Field(description="Information about the vehicle involved.")

class InvestigationReportSchema(BaseModel):
    Classification: str = Field(description="Type or classification of the incident (e.g., 'Theft', 'Burglary').")
    EventDate: str = Field(description="The date the event occurred, formatted as DD/MM/YYYY. If the text says 'today' or 'yesterday', retain it as-is.")
    EventTime: str = Field(description="The time the event occurred in 24-hour HH:MM format (e.g., '08:45', '14:30').")
    EventLocation: AddressSchema = Field(description="The location where the incident occurred.")
    Victim: PersonSchema = Field(description="Information about the victim.")
    StolenVehicle: Optional[VehicleSchema] = Field(default=None, description="Details of the vehicle that was stolen, if any.")
    SuspectVehicle: Optional[VehicleSchema] = Field(default=None, description="Details of a vehicle used by a suspect, if any.")

class TheftFromMotorVehicleSchema(BaseModel):
    Classification: str = Field(
        description="Type of offence - either 'Theft From Motor Vehicle' or 'Vehicle Interference'"
    )
    EventDate: str = Field(
        description="The date when the theft occurred in DD/MM/YYYY format."
    )
    EventTime: str = Field(
        description="The time of the theft in 24-hour HH:MM format."
    )
    Vehicle: VehicleSchema = Field(
        description="Information about the vehicle that was broken into."
    )
    Victim: PersonSchema = Field(
        description="Information about the owner/victim of the vehicle."
    )
    VehicleDamage: Optional[str] = Field(
        default="",
        description="Description of any damage to the vehicle, if applicable."
    )
    CCTVAvailable: bool = Field(
        description="Whether CCTV footage is available."
    )
    CCTVLocation: Optional[str] = Field(
        default="",
        description="Location where CCTV footage can be accessed, if available."
    )
    StolenItems: Optional[List[str]] = Field(
        default=[],
        description="List of items stolen from the vehicle."
    )
    EventLocation: Optional[AddressSchema] = Field(
        default=None,
        description="Location where the theft occurred."
    )