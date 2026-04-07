from pydantic import BaseModel,field_validator,EmailStr
from utils.validator import validate_password
import re
from datetime import date,datetime
from typing import Optional,List

class Trainer_update_request(BaseModel):
    trainer_name: str
    trainer_number: str
    trainer_email: EmailStr
    trainer_gender: str
    trainer_dob: date
    trainer_city: str
    trainer_state: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "trainer_name": "trainer123",
                "trainer_number": "7299422096",
                "trainer_email": "trainer@gmail.com",
                "trainer_gender": "male",
                "trainer_dob": "2004-09-05",
                "trainer_city": "chennai",
                "trainer_state": "tamilnadu",
                "password": "trainer@1234"
            }
        }

class Trainer_email(BaseModel):
    trainer_email:EmailStr

class Trainerrequest(BaseModel):
    trainer_email: EmailStr
    trainer_name: str 
    trainer_pass :str
    trainer_number: int
    trainer_dob: date
    trainer_city: str
    trainer_state: str

    @field_validator("trainer_name")
    @classmethod
    def validate_username(cls, value: str):
        if " " in value:
            raise ValueError("Username must not contain spaces")
        if not re.fullmatch(r"[A-Za-z]+", value):
            raise ValueError("Username must contain only letters")
        return value
    
    
    @field_validator("trainer_number")
    @classmethod
    def validate_phone(cls, value: int):
        if not isinstance(value, int):
            raise ValueError("Phone number must be an integer")
        if len(str(value)) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return value
    
    _validate_password = field_validator("trainer_pass")(validate_password)

class trainer_request_get(BaseModel):
    trainer_email: EmailStr
    class Config:
        json_schema_extra = {
            "example": {
                "trainer_email": "trainer@gmail.com"
            }
        }

class CreateCategory(BaseModel):
    Category_Name: str
    slug: Optional[str]
    Parent_ID: Optional[str]=None
    Course_Description: str
    Icon: Optional[str]
    Thumbnail: str

    class Config:
        json_schema_extra = {
            "example": {
                "Category_Name": "Programming",
                "slug": "programming",
                "Parent_ID": None,
                "Course_Description": "Programming related courses",
                "Icon": "programming-icon.png",
                "Thumbnail": "programming-thumbnail.png"
            }
        }

class CategoryResponse(BaseModel):
    Category_ID: str
    Category_Name: str
    slug: Optional[str]
    Parent_ID: Optional[str]
    Course_Description: str
    Icon: Optional[str]
    Thumbnail: str
    created_at: datetime

    class Config:
        from_attributes = True

class SubCategoryResponse(BaseModel):
    Category_ID: str
    Category_Name: str
    slug: Optional[str]
    Course_Description: str
    Icon: Optional[str]
    Thumbnail: str

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    Category_ID: str
    Category_Name: str
    slug: Optional[str]
    Course_Description: str
    Icon: Optional[str]
    Thumbnail: str
    subcategories: List[SubCategoryResponse] = []

    class Config:
        from_attributes = True


class AllCategoriesResponse(BaseModel):
    categories: List[CategoryResponse]

class UpdateCategory(BaseModel):
    Category_Name: Optional[str]
    slug: Optional[str]
    Parent_ID: Optional[str] = None
    Course_Description: Optional[str]
    Icon: Optional[str]
    Thumbnail: Optional[str]

class CategoryResponse(BaseModel):
    Category_ID: str
    Category_Name: str
    slug: Optional[str]
    Parent_ID: Optional[str]
    Course_Description: str
    Icon: Optional[str]
    Thumbnail: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CreateCourseRequest(BaseModel):
    category_id: str
    course_Type:str
    course_title: str
    course_description: str
    skill_set: str
    required_knowledge: str
    benefits: str
    thumbnail: str
    duration: str
    level: str
    language: str
    original_pay: int
    discount_pay: int

    class Config:
        schema_extra = {
            "example": {
                "category_id": "CAT-001",
                "course_Type":"Live",
                "course_title": "Python FastAPI Masterclass",
                "course_description": "Learn how to build high-performance APIs using FastAPI",
                "skill_set": "Python, FastAPI, REST API",
                "required_knowledge": "Basic Python programming",
                "benefits": "Build real-world backend applications",
                "thumbnail": "https://cdn.example.com/course/python-fastapi.png",
                "duration": "40 hours",
                "level": "Beginner",
                "language": "English",
                "original_pay": 5000,
                "discount_pay": 1999
            }
        }

class CourseResponse(BaseModel):
    status: bool
    message: str
    course_id: str

    class Config:
        schema_extra = {
            "example": {
                "status": True,
                "message": "Course created successfully",
                "course_id": "COURSE-123456"
            }
        }

class CreateCourseDemoRequest(BaseModel):
    course_id: str
    title: str
    video_url: str
    duration: str

    class Config:
        schema_extra = {
            "example": {
                "course_id": "COURSE-12345",
                "title": "Course Introduction",
                "video_url": "https://cdn.example.com/demo.mp4",
                "duration": "10 minutes"
            }
        }

class CourseDemoResponse(BaseModel):
    status: bool
    message: str
    demo_id: str

    class Config:
        schema_extra = {
            "example": {
                "status": True,
                "message": "Course demo added successfully",
                "demo_id": "DEMO-12345"
            }
        }

class CreateModuleRequest(BaseModel):
    Course_ID: str
    Title: str 
    Course_Description: str 
    Position: int 

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-12345",
                "Title": "Introduction to Python",
                "Course_Description": "This module covers python basics",
                "Position": 1
            }
        }

class CreateModuleResponse(BaseModel):
    Module_ID: str
    Course_ID: str
    Title: str
    Course_Description: str
    Position: int
    created_at: datetime

    class Config:
        orm_mode = True


class CreateNotesRequest(BaseModel):
    Course_ID: str
    Title: str 
    File_URL: str 
    File_Type: str 

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-1001",
                "Title": "Python Variables Notes",
                "File_URL": "https://cdn.gyantree.com/notes/python_variables.pdf",
                "File_Type": "pdf"
            }
        }

class CreateNotesResponse(BaseModel):
    Notes_ID: str
    Course_ID: str
    Title: str
    File_URL: str
    File_Type: str
    created_at: datetime

    class Config:
        orm_mode = True
    
class CreateVideoRequest(BaseModel):

    Course_ID: str 
    Module_ID: str 
    Video_URL: str 
    course_description: str

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-1001",
                "Module_ID": "MODULE-2001",
                "Video_URL": "https://cdn.gyantree.com/videos/python_intro.mp4",
                "course_description": "Introduction to Python video"
            }
        }

class CreateVideoResponse(BaseModel):

    Video_ID: str
    Module_ID: str
    Course_ID: str
    Video_URL: str
    course_description: str
    created_at: datetime

    class Config:
        orm_mode = True

class CreateLiveCourseRequest(BaseModel):

    Course_ID: str
    Module_ID: str
    Title: str
    Start_time: datetime
    End_time: datetime
    Status: str

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-1001",
                "Module_ID": "MODULE-2001",
                "Title": "Python Live Session 1",
                "Start_time": "2026-03-20T10:00:00+05:30",
                "End_time": "2026-03-20T11:30:00+05:30",
                "Status": "Scheduled"
            }
        }

class CreateLiveCourseResponse(BaseModel):

    Live_ID: str
    Module_ID: str
    Course_ID: str
    Meeting_URL: str
    Provider: str
    Start_time: datetime
    End_time: datetime
    Status: str
    created_at: datetime

    class Config:
        orm_mode = True

class CreateRecVideoRequest(BaseModel):

    Course_ID: str 
    Live_ID: str 
    Rec_Video_URL: str 
    Duration: str 

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-1001",
                "Live_ID": "LIVE-2001",
                "Rec_Video_URL": "https://cdn.gyantree.com/recordings/session1.mp4",
                "Duration": "1h 20m"
            }
        }
    
class CreateRecVideoResponse(BaseModel):

    Rec_Video_ID: str
    Live_ID: str
    Course_ID: str
    Rec_Video_URL: str
    Duration: str
    created_at: datetime

    class Config:
        orm_mode = True

class CreateAssessmentRequest(BaseModel):

    Module_ID: str 
    Title: str 
    Description: str 

    Total_Mark: int 
    Passing_Mark: int 

    Duration: int 
    Attempt_Limit: int

    Status: str 

    class Config:
        schema_extra = {
            "example": {
                "Module_ID": "MODULE-2001",
                "Title": "Python Basics Test",
                "Description": "Assessment for python fundamentals",
                "Total_Mark": 100,
                "Passing_Mark": 40,
                "Duration": 30,
                "Attempt_Limit": 3,
                "Status": "Active"
            }
        }

class CreateAssessmentResponse(BaseModel):

    Assessment_ID: str
    Module_ID: str
    Title: str
    Description: str
    Total_Mark: int
    Passing_Mark: int
    Duration: int
    Attempt_Limit: int
    Status: str
    created_at: datetime

    class Config:
        orm_mode = True

class CreateQuestionRequest(BaseModel):

    Assessment_ID: str 
    Question_Txt: str 
    Mark: int 
    Question_Type: str 
    Explanation: str 
    Position: int 

    class Config:
        schema_extra = {
            "example": {
                "Assessment_ID": "ASSESS-1001",
                "Question_Txt": "What is Python?",
                "Mark": 5,
                "Question_Type": "MCQ",
                "Explanation": "Python is a high level programming language",
                "Position": 1
            }
        }
    
class CreateQuestionResponse(BaseModel):

    Question_ID: str
    Assessment_ID: str
    Question_Txt: str
    Mark: int
    Question_Type: str
    Explanation: str
    Position: int
    created_at: datetime

    class Config:
        orm_mode = True

class CreateOptionRequest(BaseModel):

    Question_ID: str 
    Option_Txt: str 
    Is_Correct: bool 
    Position: int 

    class Config:
        schema_extra = {
            "example": {
                "Question_ID": "QUES-1001",
                "Option_Txt": "Python is a programming language",
                "Is_Correct": True,
                "Position": 1
            }
        }

class CreateOptionResponse(BaseModel):

    Option_ID: str
    Question_ID: str
    Option_Txt: str
    Is_Correct: bool
    Position: int
    created_at: datetime

    class Config:
        orm_mode = True


class UpdateCourseRequest(BaseModel):
    category_id: str 
    course_Type: str 
    course_title: str 
    course_description: str 
    skill_set: str 
    required_knowledge: str 
    benefits: str 
    thumbnail: str
    duration: str 
    level: str 
    language: str
    original_pay: float 
    discount_pay: float 

    class Config:
        schema_extra = {
            "example": {
                "category_id": "CAT-1001",
                "course_Type": "Recorded",
                "course_title": "Python Full Stack Development",
                "course_description": "Complete Python backend and API development course",

                "skill_set": "Python, FastAPI, SQLAlchemy, REST APIs",
                "required_knowledge": "Basic Python knowledge",
                "benefits": "Become a backend developer and build scalable APIs",

                "thumbnail": "https://cdn.example.com/python-course.png",
                "duration": "40 hours",

                "level": "Beginner",
                "language": "English",

                "original_pay": 4999,
                "discount_pay": 1999
            }
        }

class UpdateCourseResponse(BaseModel):

    status: bool
    message: str
    course_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Course updated successfully",
                "course_id": "COURSE-7a92c1c0-7c8e-4b3d-b8c4-123456"
            }
        }

class UpdateCourseDemoRequest(BaseModel):

    title: str 
    video_url: str
    duration: str 

    class Config:
        schema_extra = {
            "example": {
                "title": "Python Course Introduction",
                "video_url": "https://cdn.example.com/demo/python-intro.mp4",
                "duration": "10 minutes"
            }
        }

class UpdateCourseDemoResponse(BaseModel):

    status: bool
    message: str
    demo_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Course demo updated successfully",
                "demo_id": "DEMO-123456"
            }
        }

class UpdateModuleRequest(BaseModel):

    Title: str 
    Course_Description: str

    class Config:
        schema_extra = {
            "example": {
                "Title": "Introduction to Python",
                "Course_Description": "This module covers Python basics"
            }
        }

class UpdateModuleResponse(BaseModel):

    status: bool
    message: str
    module_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Module updated successfully",
                "module_id": "MODULE-12345"
            }
        }

class UpdateNotesRequest(BaseModel):

    Title: str
    File_URL: str
    File_Type: str

    class Config:
        schema_extra = {
            "example": {
                "Title": "Python Variables Notes",
                "File_URL": "https://cdn.example.com/python_variables.pdf",
                "File_Type": "pdf"
            }
        }

class UpdateNotesResponse(BaseModel):

    status: bool
    message: str
    notes_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Notes updated successfully",
                "notes_id": "NOTES-12345"
            }
        }

class UpdateVideoRequest(BaseModel):

    Module_ID: str 
    Course_ID: str 
    Video_URL: str 
    course_description: str 

    class Config:
        schema_extra = {
            "example": {
                "Module_ID": "MODULE-12345",
                "Course_ID": "COURSE-12345",
                "Video_URL": "https://cdn.example.com/videos/python_intro.mp4",
                "course_description": "Introduction to Python programming"
            }
        }

class UpdateVideoResponse(BaseModel):

    status: bool
    message: str
    video_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Video updated successfully",
                "video_id": "VIDEO-12345"
            }
        }

class UpdateLiveCourseRequest(BaseModel):

    Course_ID: str 
    Module_ID: str 
    Meeting_URL: str 
    Provider: str 
    Start_time: datetime 
    End_time: datetime 
    Status: str 

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-12345",
                "Module_ID": "MODULE-12345",
                "Meeting_URL": "https://zoom.us/j/123456789",
                "Provider": "Zoom",
                "Start_time": "2026-03-20T10:00:00",
                "End_time": "2026-03-20T11:00:00",
                "Status": "Scheduled"
            }
        }

class UpdateLiveCourseResponse(BaseModel):

    status: bool
    message: str
    live_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Live session updated successfully",
                "live_id": "LIVE-12345"
            }
        }

class UpdateRecVideoRequest(BaseModel):

    Course_ID: str 
    Live_ID: str 
    Rec_Video_URL: str 
    Duration: str 

    class Config:
        schema_extra = {
            "example": {
                "Course_ID": "COURSE-12345",
                "Live_ID": "LIVE-12345",
                "Rec_Video_URL": "https://cdn.example.com/recordings/session1.mp4",
                "Duration": "1 hour"
            }
        }

class UpdateRecVideoResponse(BaseModel):

    status: bool
    message: str
    rec_video_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Recorded video updated successfully",
                "rec_video_id": "RECVIDEO-12345"
            }
        }

class UpdateAssessmentRequest(BaseModel):

    Module_ID: str 
    Title: str 
    Description: str 
    Total_Mark: int 
    Passing_Mark: int 
    Duration: int 
    Attempt_Limit: int 
    Status: str 

    class Config:
        schema_extra = {
            "example": {
                "Module_ID": "MODULE-12345",
                "Title": "Python Basics Test",
                "Description": "Assessment for Python fundamentals",
                "Total_Mark": 100,
                "Passing_Mark": 40,
                "Duration": 30,
                "Attempt_Limit": 3,
                "Status": "Active"
            }
        }
    
class UpdateAssessmentResponse(BaseModel):

    status: bool
    message: str
    assessment_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Assessment updated successfully",
                "assessment_id": "ASSESS-12345"
            }
        }

class UpdateQuestionRequest(BaseModel):

    Assessment_ID: str
    Question_Txt: str
    Mark: int 
    Question_Type: str
    Explanation: str 


    class Config:
        schema_extra = {
            "example": {
                "Assessment_ID": "ASSESS-12345",
                "Question_Txt": "What is Python?",
                "Mark": 5,
                "Question_Type": "MCQ",
                "Explanation": "Python is a high-level programming language"
            }
        }

class UpdateQuestionResponse(BaseModel):

    status: bool
    message: str
    question_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Question updated successfully",
                "question_id": "QUES-12345"
            }
        }

class UpdateOptionRequest(BaseModel):

    Question_ID: str 
    Option_Txt: str 
    Is_Correct: bool 

    class Config:
        schema_extra = {
            "example": {
                "Question_ID": "QUES-12345",
                "Option_Txt": "Python is a programming language",
                "Is_Correct": True
            }
        }

class UpdateOptionResponse(BaseModel):

    status: bool
    message: str
    option_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "status": True,
                "message": "Option updated successfully",
                "option_id": "OPT-12345"
            }
        }

class SwapQuestionRequest(BaseModel):
    question_id_1: str
    question_id_2: str

class SwapOptionRequest(BaseModel):
    option_id_1: str
    option_id_2: str

class ActivationResponse(BaseModel):
    status: str
    message: str


class SwapModuleRequest(BaseModel):
    module_id_1: str
    module_id_2: str

class ResetAssessmentResponse(BaseModel):
    message: str

class EnrollmentStat(BaseModel):
    course_id: str
    course_title: str
    enrolled_students: int

class EnrollmentStatsResponse(BaseModel):
    status: bool
    data: List[EnrollmentStat]

class StudentProgressDetail(BaseModel):
    user_id: str
    user_name: Optional[str]
    progress_percentage: int
    completed_modules: int
    total_modules: int

class CourseStudentsProgressResponse(BaseModel):
    status: bool
    course_id: str
    data: List[StudentProgressDetail]