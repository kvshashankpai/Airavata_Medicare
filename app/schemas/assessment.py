from typing import Any
from pydantic import BaseModel

class ExtractionResult(BaseModel):
    intent: str = 'burn_case'
    extracted_information: dict[str, Any] = {}
    corrections: dict[str, Any] = {}

class AssessmentOut(BaseModel):
    age: str
    cause_of_burn: str
    time_since_burn: str
    first_aid_given: str
    body_part_affected: str
    approximate_size: str
    blistering_or_skin_appearance: str
    pain_level: str
    circumferential: str
    smoke_or_enclosed_space_exposure: str
    missing_information: list[str]
