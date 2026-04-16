from datetime import date
from pydantic import ValidationError
from fastapi import BackgroundTasks, FastAPI,HTTPException,Request,APIRouter,Depends, UploadFile, File,Form,Path,Query,status
from h11 import Data
from Database.DB import get_db
from sqlalchemy.orm import Session
from services.AuthService import admin_Authorization
from schemas.user import GenderEnum
from services.AdminService import AdminService
from schemas.admin import Trainerrequest,trainer_request_get,Trainer_update_request,Trainer_status_update,CreateCategory,CategoryResponse,AllCategoriesResponse,UpdateCategory,CreateCourseRequest,CourseResponse,CourseDemoResponse,CreateCourseDemoRequest,CreateModuleRequest,CreateModuleResponse,CreateNotesRequest,CreateNotesResponse,CreateVideoRequest,CreateVideoResponse,CreateLiveCourseRequest,CreateLiveCourseResponse,CreateRecVideoRequest,CreateRecVideoResponse,CreateAssessmentRequest,CreateAssessmentResponse,CreateQuestionRequest,CreateQuestionResponse,CreateOptionRequest,CreateOptionResponse,SubCategoryResponse,UpdateCourseRequest,UpdateCourseResponse,UpdateCourseDemoRequest,UpdateCourseDemoResponse,UpdateModuleRequest,UpdateModuleResponse,UpdateNotesRequest,UpdateNotesResponse,UpdateVideoRequest,UpdateVideoResponse,UpdateLiveCourseRequest,UpdateLiveCourseResponse,UpdateRecVideoRequest,UpdateRecVideoResponse,UpdateAssessmentRequest,UpdateAssessmentResponse,UpdateQuestionRequest,UpdateQuestionResponse,UpdateOptionRequest,UpdateOptionResponse,SwapQuestionRequest,SwapOptionRequest,ActivationResponse,SwapModuleRequest
from typing import Annotated
from schemas.admin import EnrollmentStatsResponse,CourseStudentsProgressResponse, AllFeedbackAdminResponse, FeedbackStatusUpdateRequest
from schemas.admin import ResetAssessmentResponse
from services.ProgressService import ProgressService

router_admin= APIRouter()

@router_admin.post("/create_trainer",
summary="Create Trainer Profile",
description="Creates a trainer profile with the provided information.")
async def create_trainer(
    trainer_email: Annotated[str, Form(..., examples=["trainer@gmail.com"])],
    trainer_name: Annotated[str, Form(..., examples=["ArulJayaraj"])],
    trainer_number: Annotated[int, Form(..., examples=[1234567890])],
    trainer_pass: Annotated[str, Form(..., examples=["log@1234"])],
    trainer_dob: Annotated[date, Form(..., examples=["1990-01-01"])],
    trainer_gender: Annotated[GenderEnum, Form(..., examples=["male"])],
    trainer_city: Annotated[str, Form(..., examples=["New York"])],
    trainer_state: Annotated[str, Form(..., examples=["NY"])],
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    token: object = Depends(admin_Authorization())
):
    try:
        Data = Trainerrequest(
            trainer_email=trainer_email,
            trainer_name=trainer_name,
            trainer_pass=trainer_pass,
            trainer_number=trainer_number,
            trainer_dob=trainer_dob,
            trainer_city=trainer_city,
            trainer_state=trainer_state
        )
        return await AdminService().create_trainer_services(Data,trainer_gender,background_tasks,token, db)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail= str(e)
        )

@router_admin.post("/get_trainer",summary="Get Trainer Profile",
    description="Retrieves the profile information of the authenticated trainer.")
async def get_trainer(Data:trainer_request_get,db: Session = Depends(get_db),token: object = Depends(admin_Authorization())):
    return await AdminService().get_trainer_profile(Data,token, db)

@router_admin.get("/all_trainer",summary="all Trainer email",
    description="Retrieves the email of the  trainer.")
async def all_trainer_email(db: Session = Depends(get_db),token: object = Depends(admin_Authorization())):
    return await AdminService().all_trainer_email(token, db)

@router_admin.put("/update-trainer",summary="update_trainer_profile",
    description = "To update the trainer profile by admin")
async def update_trainer_profile(Data:Trainer_update_request,db: Session = Depends(get_db),token: object = Depends(admin_Authorization())):
    return await AdminService().update_trainer_service(Data,db,token)

@router_admin.put("/inactive-trainer",summary="update trainer status",description="activate or inactivate trainer")
async def update_trainer_status(Data:Trainer_status_update,db: Session = Depends(get_db),token: object = Depends(admin_Authorization())):
    return await AdminService().update_trainer_status(Data,token, db)

@router_admin.post("/create-category",response_model=CategoryResponse,summary="Create Course Category",description="""Allows an admin to create a new course category. 
If Parent_ID is provided, the category will be created as a subcategory.If Parent_ID is null, it will be created as a main category.""")
async def create_category(data: CreateCategory,db: Session = Depends(get_db),token : object = Depends(admin_Authorization())):
    return await AdminService().create_category(data, db,token)

@router_admin.get("/get-categories",response_model=AllCategoriesResponse,summary="Get All Categories",description="Fetch all course categories with their subcategories in a hierarchical structure.")
async def get_all_categories(db: Session = Depends(get_db)):
    return await AdminService().get_all_categories(db, None)

@router_admin.put("/update-category/{category_id}",response_model=CategoryResponse,summary="Update Category",description="Allows admin to update category information.")
async def update_category(category_id: str,data: UpdateCategory,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_category(category_id, data, db,token)

@router_admin.delete("/delete-category/{category_id}",summary="Delete Category",description="Deletes a category only if no courses are assigned to it.")
async def delete_category(category_id: str,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_category(category_id, db,token)


"""
1. Create Course
2. Add Demo to Course
3. Add Module to Course
4. Add Video to Module
5. Add Live Session to Module
6. Add Notes
7. Add Assessment to Module
8. Add Question to Assessment
9. Add Option to Question
"""

@router_admin.post("/create_course", response_model=CourseResponse,summary="Create a new course",description="""This allows an admin to create a new course in the LMS.""")
async def create_course(data: CreateCourseRequest,instructor_id: str = Query(...,example="USER-12345",description="Unique ID of the instructor assigned to the course"),background_tasks: BackgroundTasks = BackgroundTasks(),db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_course(data, instructor_id, db,background_tasks,token)

@router_admin.post("/add_course_demo",response_model=CourseDemoResponse,summary="Add course demo",description="This API allows admin or instructor to add a demo video for a course.")
async def add_course_demo(data: CreateCourseDemoRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_course_demo(data, db)

@router_admin.post("/create_module",response_model=CreateModuleResponse,summary="Create Course Module",description="API to create a new module inside a course")
async def create_module(data: CreateModuleRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_module_service(data, db)

@router_admin.post("/create_notes",response_model=CreateNotesResponse,summary="Create Course Notes",description="Upload or register notes for a course")
async def create_notes(data: CreateNotesRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_notes_service(data, db)

@router_admin.post("/create_video",response_model=CreateVideoResponse,summary="Create Course Video",description="Add video to recorded course module")
async def create_video(data: CreateVideoRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_video_service(data, db)

@router_admin.post("/create_live_session",response_model=CreateLiveCourseResponse,summary="Create Live Course Session",description="Create a live meeting session for live courses")
async def create_live_session(data: CreateLiveCourseRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_live_course_service(data, db)

@router_admin.post("/create_recorded_video",response_model=CreateRecVideoResponse,summary="Create Recorded Live Video",description="Upload recorded video for live course session")
async def create_recorded_video(data: CreateRecVideoRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_recorded_video_service(data, db)

@router_admin.post("/create_assessment",response_model=CreateAssessmentResponse,summary="Create Assessment",description="Create assessment for a course module")
async def create_assessment(data: CreateAssessmentRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_assessment_service(data, db)

@router_admin.post("/create_question",response_model=CreateQuestionResponse,summary="Create Question",description="Create question for assessment")
async def create_question(data: CreateQuestionRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_question_service(data, db)

@router_admin.post("/create_option",response_model=CreateOptionResponse,summary="Create Question Option",description="Create option for assessment question")
async def create_option(data: CreateOptionRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().create_option_service(data, db)

@router_admin.put("/update_course/{course_id}",response_model=UpdateCourseResponse,summary="Update Course",description="Update an existing course")
async def update_course(course_id: str,data: UpdateCourseRequest,instructor_id: str = Query(..., example="USER-12345"),db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_course(course_id,data,instructor_id,db,token)

@router_admin.put("/update_course_demo/{demo_id}",response_model=UpdateCourseDemoResponse,summary="Update course demo",description="Update demo video for a course")
async def update_course_demo(demo_id: str,data: UpdateCourseDemoRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_course_demo(demo_id, data, db)

@router_admin.put("/update_module/{module_id}",response_model=UpdateModuleResponse,summary="Update Course Module",description="Update an existing module inside a course")
async def update_module(module_id: str,data: UpdateModuleRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_module_service(module_id, data, db)

@router_admin.delete("/user/{user_id}/assessment/{assessment_id}/reset", response_model=ResetAssessmentResponse, summary="Reset Assessment Attempts", description="Resets failed assessment attempts for a user so they can try again.")
async def reset_assessment_api(user_id: str, assessment_id: str, db: Session = Depends(get_db), token: dict = Depends(admin_Authorization())):
    return await ProgressService().reset_assessment_attempts(
        user_id=user_id,
        assessment_id=assessment_id,
        db=db
    )

@router_admin.put("/update_notes/{notes_id}",response_model=UpdateNotesResponse,summary="Update Course Notes",description="Update notes for a course")
async def update_notes(notes_id: str,data: UpdateNotesRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_notes_service(notes_id, data, db)

@router_admin.put("/update_video/{video_id}",response_model=UpdateVideoResponse,summary="Update Course Video",description="Update video for a recorded course module")
async def update_video(video_id: str,data: UpdateVideoRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_video_service(video_id, data, db)

@router_admin.put("/update_live_session/{live_id}",response_model=UpdateLiveCourseResponse,summary="Update Live Course Session",description="Update a live session for live courses")
async def update_live_session(live_id: str,data: UpdateLiveCourseRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_live_course_service(live_id, data, db)

@router_admin.put("/update_recorded_video/{rec_video_id}",response_model=UpdateRecVideoResponse,summary="Update Recorded Live Video",description="Update recorded video for a live course session")
async def update_recorded_video(rec_video_id: str,data: UpdateRecVideoRequest,db: Session = Depends(get_db)):
    return await AdminService().update_recorded_video_service(rec_video_id, data, db)

@router_admin.put( "/update_assessment/{assessment_id}", response_model=UpdateAssessmentResponse, summary="Update Assessment", description="Update assessment for a course module")
async def update_assessment(assessment_id: str,data: UpdateAssessmentRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_assessment_service(assessment_id,data,db)

@router_admin.put("/update_question/{question_id}",response_model=UpdateQuestionResponse,summary="Update Question",description="Update a question inside an assessment")
async def update_question(question_id: str,data: UpdateQuestionRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_question_service(question_id,data,db)

@router_admin.put("/update_option/{option_id}",response_model=UpdateOptionResponse,summary="Update Question Option",description="Update option for a question")
async def update_option(option_id: str,data: UpdateOptionRequest,db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().update_option_service(option_id,data,db)

@router_admin.get("/course/{course_id}/full-details", summary="Get Full Course Structure")
async def get_full_course(course_id: str, db: Session = Depends(get_db)):
    return await AdminService().get_full_course_details(course_id, db)

@router_admin.get("/courses/ids-by-status", summary="Get Course IDs by Status")
async def get_course_ids_by_status(db: Session = Depends(get_db)):
    return await AdminService().get_course_ids_by_status(db)

@router_admin.get("/instructor/{user_id}/live-sessions", summary="Get Instructor Live Sessions")
async def get_live_sessions(user_id: str, db: Session = Depends(get_db)):
    return await AdminService().get_instructor_live_sessions(user_id, db)

@router_admin.delete(
    "/delete-course/{course_id}",
    summary="Delete Course",
    description="Deletes a course by ID. This will automatically delete all related modules, videos, notes, assessments, questions, and options due to cascade delete.",
    response_description="Course deleted successfully",
    responses={
        200: {
            "description": "Successful deletion",
            "content": {
                "application/json": {
                    "example": {
                        "status": True,
                        "message": "Course deleted successfully (full cascade)"
                    }
                }
            }
        },
        404: {
            "description": "Course not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Course not found"
                    }
                }
            }
        }
    }
)
async def delete_course(
    course_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_course_service(course_id, db)


@router_admin.delete(
    "/delete-module/{module_id}",
    summary="Delete Module",
    description="Deletes a module and all related content like videos, live sessions, assessments, questions, and options.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Module deleted successfully"
            }
        }
    }
)
async def delete_module(module_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_module_service(module_id, db)


@router_admin.delete(
    "/delete-assessment/{assessment_id}",
    summary="Delete Assessment",
    description="Deletes an assessment along with all its questions and options.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Assessment deleted successfully"
            }
        }
    }
)
async def delete_assessment(assessment_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_assessment_service(assessment_id, db)


@router_admin.delete(
    "/delete-question/{question_id}",
    summary="Delete Question",
    description="Deletes a question and all its options.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Question deleted successfully"
            }
        }
    }
)
async def delete_question(question_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_question_service(question_id, db)


@router_admin.delete(
    "/delete-option/{option_id}",
    summary="Delete Option",
    description="Deletes a single option from a question.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Option deleted successfully"
            }
        }
    }
)
async def delete_option(option_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_option_service(option_id, db)


@router_admin.delete(
    "/delete-notes/{notes_id}",
    summary="Delete Notes",
    description="Deletes course notes.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Notes deleted successfully"
            }
        }
    }
)
async def delete_notes(notes_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_notes_service(notes_id, db)


@router_admin.delete(
    "/delete-demo/{demo_id}",
    summary="Delete Demo",
    description="Deletes a course demo video.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Demo deleted successfully"
            }
        }
    }
)
async def delete_demo(demo_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_demo_service(demo_id, db)

@router_admin.delete(
    "/delete-video/{video_id}",
    summary="Delete Course Video",
    description="Deletes a recorded course video from a module.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Video deleted successfully",
                "video_id": "VIDEO-123"
            }
        },
        404: {
            "example": {"detail": "Video not found"}
        }
    }
)
async def delete_video(video_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_video_service(video_id, db)

@router_admin.delete(
    "/delete-live/{live_id}",
    summary="Delete Live Session",
    description="Deletes a live course session. Associated recorded videos will also be deleted via cascade.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Live session deleted successfully",
                "live_id": "LIVE-123"
            }
        },
        404: {
            "example": {"detail": "Live session not found"}
        }
    }
)
async def delete_live(live_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_live_service(live_id, db)

@router_admin.delete(
    "/delete-recorded-video/{rec_video_id}",
    summary="Delete Recorded Video",
    description="Deletes a recorded video associated with a completed live session.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Recorded video deleted successfully",
                "rec_video_id": "RECVIDEO-123"
            }
        },
        404: {
            "example": {"detail": "Recorded video not found"}
        }
    }
)
async def delete_recorded_video(rec_video_id: str, db: Session = Depends(get_db),token: dict = Depends(admin_Authorization())):
    return await AdminService().delete_recorded_video_service(rec_video_id, db)


@router_admin.put(
    "/swap-module-position",
    summary="Swap Module Positions",
    description="Swap the position of two modules using their Module IDs. Both modules must belong to the same course.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Module positions swapped successfully",
                "course_id": "COURSE-123",
                "data": [
                    {"module_id": "MODULE-1", "new_position": 2},
                    {"module_id": "MODULE-2", "new_position": 1}
                ]
            }
        },
        400: {
            "example": {
                "detail": "Modules must belong to the same course"
            }
        },
        404: {
            "example": {
                "detail": "One or both modules not found"
            }
        }
    }
)
async def swap_module_position_api(
    request: SwapModuleRequest,
    db: Session = Depends(get_db),
    token: dict = Depends(admin_Authorization())
):
    return await AdminService().swap_module_position(
        request.module_id_1,
        request.module_id_2,
        db
    )

@router_admin.put(
    "/swap-question-position",
    summary="Swap Question Positions",
    description="Swap the position of two questions within the same assessment using their Question IDs.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Question positions swapped successfully",
                "assessment_id": "ASSESS-123",
                "data": [
                    {"question_id": "QUES-1", "new_position": 2},
                    {"question_id": "QUES-2", "new_position": 1}
                ]
            }
        },
        400: {
            "example": {
                "detail": "Questions must belong to the same assessment"
            }
        },
        404: {
            "example": {
                "detail": "One or both questions not found"
            }
        }
    }
)
async def swap_question_position_api(
    request: SwapQuestionRequest,
    db: Session = Depends(get_db),
    token: dict = Depends(admin_Authorization())
):
    return await AdminService().swap_question_position(
        request.question_id_1,
        request.question_id_2,
        db
    )

@router_admin.put(
    "/swap-option-position",
    summary="Swap Option Positions",
    description="Swap the position of two options within the same question using their Option IDs.",
    responses={
        200: {
            "example": {
                "status": True,
                "message": "Option positions swapped successfully",
                "question_id": "QUES-123",
                "data": [
                    {"option_id": "OPT-1", "new_position": 2},
                    {"option_id": "OPT-2", "new_position": 1}
                ]
            }
        },
        400: {
            "example": {
                "detail": "Options must belong to the same question"
            }
        },
        404: {
            "example": {
                "detail": "One or both options not found"
            }
        }
    }
)
async def swap_option_position_api(
    request: SwapOptionRequest,
    db: Session = Depends(get_db),
    token: dict = Depends(admin_Authorization())
):
    service = AdminService() 

    return await service.swap_option_position(
        request.option_id_1,
        request.option_id_2,
        db
    )
@router_admin.put(
    "/activate/{course_id}",
    status_code=status.HTTP_200_OK,
    response_model=ActivationResponse,
    summary="Activate Course",
    description="""
Activate a course after validating required conditions.

Rules:
- Course type must match its content (video or live)
- Course must have at least one module
- If assessments exist:
  - Must have at least one question
  - Each question must have at least 2 options

Result:
- If valid → course becomes active and draft is disabled
- If invalid → returns an error message
""",
    responses={
        200: {
            "description": "Course activated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Course activated successfully"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Each question must have at least 2 options"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def activate_course(
    course_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: dict = Depends(admin_Authorization())
):
    service = AdminService() 

    success, message = await service.activate_course(course_id,db,background_tasks)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "status": "success",
        "message": message
    }

@router_admin.get("/enrollment-stats", response_model=EnrollmentStatsResponse, summary="Get Enrollment Statistics", description="Returns the number of students enrolled in each course.")
async def get_enrollment_stats_api(db: Session = Depends(get_db), token: dict = Depends(admin_Authorization())):
    return await AdminService().get_enrollment_stats(db)

@router_admin.get("/all-feedback", response_model=AllFeedbackAdminResponse, summary="Get All Feedback for Moderation")
async def get_all_feedback_api(db: Session = Depends(get_db), token: dict = Depends(admin_Authorization())):
    return await AdminService().get_all_feedbacks_for_moderation(db)

@router_admin.put("/feedback/{feedback_id}/status", summary="Update Feedback Display Status")
async def update_feedback_status_api(feedback_id: str, request: FeedbackStatusUpdateRequest, db: Session = Depends(get_db), token: dict = Depends(admin_Authorization())):
    return await AdminService().update_feedback_status(feedback_id, request.display_status, db)

