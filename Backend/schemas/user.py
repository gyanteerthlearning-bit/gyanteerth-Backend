from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re
from datetime import date

class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class UpdateUserProfileRequest(BaseModel):
    user_name: str 
    user_number: int
    user_dob: date
    user_city: str
    user_state: str

    @field_validator("user_name")
    @classmethod
    def validate_username(cls, value: str):
        if not re.fullmatch(r"[A-Za-z\s]+", value):
            raise ValueError("Username must contain only letters and spaces")
        return value
    
    
    @field_validator("user_number")
    @classmethod
    def validate_phone(cls, value: int):
        if not isinstance(value, int):
            raise ValueError("Phone number must be an integer")
        if len(str(value)) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return value
    
from pydantic import BaseModel
from typing import Optional
from datetime import date

class UserProfile_response(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    user_name: Optional[str] = None
    user_pic: Optional[str] = None
    user_number: Optional[int] = None
    user_dob: Optional[date] = None
    user_gender: Optional[GenderEnum] = None
    user_city: Optional[str] = None
    user_state: Optional[str] = None
    email_verified: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USER-1234-abcd",
                "email": "user_email@gmail.com",
                "user_name": "John Doe",
                "user_pic": "https://res.cloudinary.com/demo/image/upload/1234567890/user_pic.jpg",
                "user_number": 1234567890,
                "user_dob": "1990-01-01",
                "user_gender": "male",
                "user_city": "New York",
                "user_state": "NY",
                "email_verified": True
            }
        }
class update_profile_response(BaseModel):
    message: str
    user_id:str
    email:str
    user_name:str
    user_pic:str | None
    user_number:str
    user_dob:date
    user_gender:GenderEnum
    user_city:str
    user_state:str
    cloud_upload_time: float | None = None
    cloud_delete_time: float | None = None
    class Config:
        json_schema_extra = {
            "example":{
                "message": "User profile updated successfully",
                "user_id": "USER-1234-abcd",
                "email": "user@gmail.com",
                "user_name": "John Doe",
                "user_pic": "https://res.cloudinary.com/demo/image/upload/1234567890/user_pic.jpg",
                "user_number": "1234567890",
                "user_dob": "1990-01-01",
                "user_gender": "male",
                "user_city": "New York",
                "user_state": "NY",
                "cloud_upload_time": 0.5,
                "cloud_delete_time": 0.3
            }
        }

class EnrollCourseRequest(BaseModel):
    course_id: str

class EnrollCourseResponse(BaseModel):
    enrollment_id: str
    message: str

class MarkLiveAttendanceRequest(BaseModel):
    live_class_id: str
    module_id: str
    attended_live: bool = False
    watched_recording: bool = False

class MarkLiveAttendanceResponse(BaseModel):
    message: str
class SubmitAssessmentRequest(BaseModel):
    course_id: str
    module_id: str
    assessment_id: str
    answers: dict[str, str]  # mapping of question_id to selected option_id

class SubmitAssessmentResponse(BaseModel):
    message: str
    score: int
    attempt_no: int
    status: str
    passed: bool

class MarkVideoProgressRequest(BaseModel):
    course_id: str
    module_id: str
    video_id: str

class MarkVideoProgressResponse(BaseModel):
    message: str

class CourseProgressResponse(BaseModel):
    course_id: str
    total_modules: int
    completed_modules: int
    progress_percentage: int
    modules_progress: dict[str, str]  # module_id -> status
    assessments_progress: list[dict]  # array of basic stats

from datetime import datetime
from typing import List

class SubmitFeedbackRequest(BaseModel):
    Course_rating: str
    Instructor_rating: str
    Review: str

class SubmitFeedbackResponse(BaseModel):
    status: bool
    message: str
    feedback_id: str

class FeedbackPublicDetail(BaseModel):
    user_name: str
    user_pic: Optional[str]
    course_title: str
    course_rating: str
    review: str
    created_at: datetime

class PublicFeedbackResponse(BaseModel):
    status: bool
    data: List[FeedbackPublicDetail]

class CertificateDetailsResponse(BaseModel):
    uuid: str
    course_name: str
    course_duration: str
    user_name: str
    issued_date: datetime

class CertificateVerifyResponse(BaseModel):
    is_valid: bool
    data: Optional[CertificateDetailsResponse] = None


