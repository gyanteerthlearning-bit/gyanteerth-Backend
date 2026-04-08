from datetime import date
from pydantic import ValidationError
from fastapi import BackgroundTasks, FastAPI,HTTPException,Request,APIRouter,Depends, UploadFile, File,Form,Path, Query
from h11 import Data
from Database.DB import get_db
from sqlalchemy.orm import Session
from services.AuthService import user_Authorization, full_Authorization
from services.UserService import UserService
from schemas.user import UpdateUserProfileRequest,EnrollCourseRequest,EnrollCourseResponse, MarkLiveAttendanceRequest, MarkLiveAttendanceResponse
from schemas.user import GenderEnum
from schemas.user import UserProfile_response,update_profile_response, SubmitFeedbackRequest, SubmitFeedbackResponse, PublicFeedbackResponse
from typing import Annotated, Optional

router_user = APIRouter()

@router_user.get("/profile",response_model =UserProfile_response,summary="Get User Profile",
    description="Retrieves the profile information of the authenticated user.")
async def get_profile(db: Session = Depends(get_db),token: object = Depends(user_Authorization())):
    return await UserService().get_user_profile(token, db)

@router_user.put(
    "/update_profile",
    response_model=update_profile_response,
    summary="Update User Profile",
    description="Updates the profile information of the authenticated user."
)
async def update_profile(
    user_name: Annotated[str, Form(..., example="ArulJayaraj")],
    user_number: Annotated[int, Form(..., example=1234567890)],
    user_dob: Annotated[date, Form(..., example="1990-01-01")],
    user_gender: Annotated[GenderEnum, Form(..., example="male")],
    user_city: Annotated[str, Form(..., example="New York")],
    user_state: Annotated[str, Form(..., example="NY")],
    user_pic: UploadFile | None = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    token: object = Depends(user_Authorization())
):
    try:
        Data = UpdateUserProfileRequest(
            user_name=user_name,
            user_number=user_number,
            user_dob=user_dob,
            user_city=user_city,
            user_state=user_state
        )

        return await UserService().update_user_profile(
            Data, user_gender, background_tasks, user_pic, token, db
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router_user.post("/enroll_course", response_model=EnrollCourseResponse)
async def enroll_course_api(request: EnrollCourseRequest, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):

    try:
        result = await UserService().enroll_course(
            course_id=request.course_id,
            db=db,
            token=token
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router_user.get("/enrolled_courses", summary="Get Enrolled Courses", description="Fetches all courses a user is enrolled in.")
async def enrolled_courses_detail(db:Session = Depends(get_db),token: object = Depends(user_Authorization())):
    return await UserService().enrolled_course(db,token)

@router_user.post("/mark-live-attendance", response_model=MarkLiveAttendanceResponse, summary="Mark Live Attendance", description="Allows a user to mark that they attended a live session or watched the recording.")
async def mark_live_attendance_api(request: MarkLiveAttendanceRequest, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    return await UserService().mark_live_attendance(
        live_class_id=request.live_class_id,
        module_id=request.module_id,
        attended_live=request.attended_live,
        watched_recording=request.watched_recording,
        token=token,
        db=db
    )

from schemas.user import SubmitAssessmentRequest, SubmitAssessmentResponse, MarkVideoProgressRequest, MarkVideoProgressResponse, CourseProgressResponse
from services.ProgressService import ProgressService

@router_user.post("/mark-video-progress", response_model=MarkVideoProgressResponse, summary="Mark Video Progress")
async def mark_video_progress_api(request: MarkVideoProgressRequest, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user_id = token.get("user_id")
    return await ProgressService().mark_video_progress(
        user_id=user_id,
        course_id=request.course_id,
        module_id=request.module_id,
        video_id=request.video_id,
        db=db
    )

@router_user.post("/submit-assessment", response_model=SubmitAssessmentResponse, summary="Submit Assessment")
async def submit_assessment_api(request: SubmitAssessmentRequest, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user_id = token.get("user_id")
    return await ProgressService().submit_assessment(
        user_id=user_id,
        course_id=request.course_id,
        module_id=request.module_id,
        assessment_id=request.assessment_id,
        answers=request.answers,
        db=db
    )

@router_user.get("/course/{course_id}/progress", response_model=CourseProgressResponse, summary="Get Course Progress")
async def get_course_progress_api(course_id: str, student_id: Optional[str] = Query(None), db: Session = Depends(get_db), token: dict = Depends(full_Authorization())):
    user_id = token.get("user_id")
    role = token.get("role").lower()
    
    target_user_id = user_id
    if student_id and role in ["admin", "trainer"]:
        target_user_id = student_id
        
    return await ProgressService().get_course_progress(
        user_id=target_user_id,
        course_id=course_id,
        db=db
    )

@router_user.post("/course/{course_id}/feedback", response_model=SubmitFeedbackResponse, summary="Submit Course Feedback")
async def submit_course_feedback_api(course_id: str, request: SubmitFeedbackRequest, db: Session = Depends(get_db), token: dict = Depends(user_Authorization())):
    user_id = token.get("user_id")
    return await UserService().submit_course_feedback(user_id, course_id, request, db)

@router_user.get("/public-feedback", response_model=PublicFeedbackResponse, summary="Get Approved Public Feedback")
async def get_public_feedback_api(db: Session = Depends(get_db)):
    return await UserService().get_public_feedbacks(db)