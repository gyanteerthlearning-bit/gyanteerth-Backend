import uuid
import random
from datetime import datetime, timedelta
from aiohttp import request
from sqlalchemy.orm import Session
from fastapi import HTTPException,Request,Depends,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from Models.User_Tables.User_Profile import user_profile_table
from Models.User_Tables.User_Refresh_Token import user_refresh_token_table
from Models.User_Tables.User_OTP import user_otp_table
from Models.User_Tables.User_Access import user_access_table
from utils.Emailservice import send_email
from sqlalchemy.exc import IntegrityError
from Database.DB import get_db
from utils.email_templates.otp_design import otp_email_template,forget_password_email_template
from utils.security import hash_password, verify_password
from utils.security import create_access_token, decode_token
from utils.security import create_refresh_token,create_forget_token
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import Request
import dotenv
import os
dotenv.load_dotenv()

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


class user_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(user_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request ):
        credentials: HTTPAuthorizationCredentials = await super(user_Authorization, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization code")
        try:
            token = decode_token(credentials.credentials)
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            if token.get("role").lower() != "user":
                raise HTTPException(status_code=403, detail="Permission denied")
            return token
        
        except HTTPException:
            raise   
        except Exception as e:
            print("Token decode error:", e)
            raise HTTPException(status_code=401, detail=str(e))

class admin_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(admin_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request ):
        credentials: HTTPAuthorizationCredentials = await super(admin_Authorization, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization code")
        try:
            token = decode_token(credentials.credentials)
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            if token.get("role").lower() != "admin":
                raise HTTPException(status_code=403, detail="Permission denied")
            return token
        
        except HTTPException:
            raise   
        except Exception as e:
            print("Token decode error:", e)
            raise HTTPException(status_code=401, detail=str(e))

class trainer_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(trainer_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request ):
        credentials: HTTPAuthorizationCredentials = await super(trainer_Authorization, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization code")
        try:
            token = decode_token(credentials.credentials)
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            if token.get("role").lower() not in ["trainer", "admin"]:
                raise HTTPException(status_code=403, detail="Permission denied")
            return token
        
        except HTTPException:
            raise   
        except Exception as e:
            print("Token decode error:", e)
            raise HTTPException(status_code=401, detail=str(e))

class full_Authorization(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(full_Authorization, self).__init__(auto_error=auto_error)
    async def __call__(self, request: Request ):
        credentials: HTTPAuthorizationCredentials = await super(full_Authorization, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization code")
        try:
            token = decode_token(credentials.credentials)
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")

            if token.get("role").lower() not in ["user", "trainer", "admin"]:
                raise HTTPException(status_code=403, detail="Permission denied")
            return token
        
        except HTTPException:
            raise   
        except Exception as e:
            print("Token decode error:", e)
            raise HTTPException(status_code=401, detail=str(e))

class AuthService:

    async def check_email(self, data, db: Session):
        result = db.query(user_profile_table, user_otp_table).outerjoin(
            user_otp_table,
            user_profile_table.user_id == user_otp_table.user_id
        ).filter(
            user_profile_table.user_email == data.email
        ).first()
        user,otp_record  = None,None
        if result:
            user, otp_record = result
            if user.user_email_verified:
                return {
                    "exists": True,
                    "message": "You already have an account"
                }
        otp = str(random.randint(100000, 999999))
        if not user:
            user = user_profile_table(
                user_id=f"USER-{uuid.uuid4()}",
                user_email=data.email,
                user_email_verified=False,
                Status = "Active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        expires_time = datetime.utcnow() + timedelta(minutes=5)
        if otp_record:
            otp_record.otp = otp
            otp_record.expires_at = expires_time
            otp_record.is_used = False
        else:
            otp_record = user_otp_table(
                otp_id=str(uuid.uuid4()),
                user_id=user.user_id,
                otp=otp,
                expires_at=expires_time,
                is_used=False
            )
            db.add(otp_record)
        db.commit()
        subject = "Gyanteerth Security Code – Verify Your Email"
        body = otp_email_template(otp)
        # Sending email directly (await) instead of background task
        # so it works reliably on free-tier deployments
        await send_email(data.email, subject, body)
        return {
            "exists": False,
            "message": "OTP sent to your email",
            "user_id": user.user_id
        }
    
    async def delete_user_profile_service(self, user_id, db: Session):
        try:
            db.query(user_otp_table).filter(
                user_otp_table.user_id == user_id
            ).delete()
            deleted = db.query(user_profile_table).filter(
                user_profile_table.user_id == user_id
            ).delete()
            if not deleted:
                raise HTTPException(status_code=404, detail="User not found")
            db.commit()
            return {
                "success": True,
                "message": "User profile deleted successfully"
            }
        except IntegrityError as e:
            db.rollback()
            return {
                "success": False,
                "message": "User account completion successful. Account cannot be deleted.",
                "system_error": str(e)
            }

    async def verify_otp_service(self, data, db: Session):
        result = (
            db.query(user_profile_table, user_otp_table)
            .join(
                user_otp_table,
                user_profile_table.user_id == user_otp_table.user_id
            )
            .filter(
                user_profile_table.user_id == data.user_id,
                user_otp_table.otp == data.otp,
                user_otp_table.is_used == False,
                user_otp_table.expires_at > datetime.utcnow()
            )
            .first()
        )
        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP or OTP expired"
            )

        user, otp_record = result
        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP"
            )
        otp_record.is_used = True
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        user.user_email_verified = True
        db.commit()
        return {
            "success": True,
            "message": "Email verified successfully"
        }
    
    async def set_password_service(self, data, request:Request ,db: Session):
    
        result = (
            db.query(
                user_profile_table,
                user_access_table,
                user_refresh_token_table
            )
            .outerjoin(
                user_access_table,
                (user_access_table.user_id == user_profile_table.user_id) &
                (user_access_table.provider_name == "Email")
            )
            .outerjoin(
                user_refresh_token_table,
                user_refresh_token_table.user_id == user_profile_table.user_id
            )
            .filter(
                user_profile_table.user_id == data.user_id,
                user_profile_table.user_email_verified == True
            )
            .first()
        )
        
        if result:
            user, existing_access, check_existing_token = result
        else:
            user, existing_access, check_existing_token = None, None, None
    
        if not user:
            return {
                "success": False,
                "message": "User not found or email not verified"
            }
    
        if existing_access:
            return {
                "success": False,
                "message": "User already has an access account"
            }
    
        refresh_token = create_refresh_token(data.user_id)

        if check_existing_token:
            check_existing_token.refresh_token = refresh_token
            check_existing_token.expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            check_existing_token.is_revoked = False
    
        else:
            user_agent = request.headers.get("user-agent", "Unknown")
            device_name = "Unknown"
            if "Windows" in user_agent:
                device_name = "Windows PC"
            elif "Android" in user_agent:
                device_name = "Android Phone"
            elif "iPhone" in user_agent:
                device_name = "iPhone"
            elif "Mac" in user_agent:
                device_name = "Mac"
            new_refresh_token = user_refresh_token_table(
                refresh_token_id=f"RefreshToken-{uuid.uuid4()}",
                user_id=data.user_id,
                refresh_token=refresh_token,
                ip_address=request.client.host,
                user_agent=user_agent,
                device_name=device_name,
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                is_revoked=False
            )
            access = user_access_table(
                access_id=f"Access-{uuid.uuid4()}",
                user_id=data.user_id,
                provider_id=f"Email-{uuid.uuid4()}",
                provider_name="Email",
                role="user",
                password_hash=hash_password(data.password)
            )
            db.add_all([access, new_refresh_token])
        db.commit()
        access_token = create_access_token(data.user_id, "user")

        return {
            "success": True,
            "message": "Successfully signed up",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def refresh_token_check_service(self, data, db: Session):
        try:
            token_data = decode_token(data.refresh_token)
    
            if not token_data or token_data.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
    
            user_id = token_data.get("user_id")
    
            token_record = db.query(user_refresh_token_table).filter(
                user_refresh_token_table.user_id == user_id,
                user_refresh_token_table.refresh_token == data.refresh_token,
                user_refresh_token_table.is_revoked == False,
                user_refresh_token_table.expires_at > datetime.utcnow()
            ).first()
    
            if not token_record:
                raise HTTPException(
                    status_code=401,
                    detail="Refresh token is invalid, revoked, or expired"
                )
    
            access_token = create_access_token(user_id, "user")
    
            return {
                "success": True,
                "access_token": access_token
            }

        except HTTPException as http_err:
        
            raise http_err
    
        except Exception as e:
            
            print(f"Error in refresh_token_check_service: {str(e)}")
    
            raise HTTPException(
                status_code=500,
                detail="Internal server error while refreshing token"
            )
    
    
    async def login_service(self, data,  request:Request, db: Session):

        result = (
            db.query(user_profile_table, user_access_table)
            .join(
                user_access_table,
                user_access_table.user_id == user_profile_table.user_id
            )
            .filter(
                user_profile_table.user_email == data.Email,
                user_profile_table.user_email_verified == True
            )
            .first()
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        user, access_record = result
        
        if not verify_password(data.password, access_record.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        user_agent = request.headers.get("user-agent", "Unknown")
        device_name = "Unknown"
    
        if "Windows" in user_agent:
            device_name = "Windows PC"
        elif "Android" in user_agent:
            device_name = "Android Phone"
        elif "iPhone" in user_agent:
            device_name = "iPhone"
        elif "Mac" in user_agent:
            device_name = "Mac"
    
        re_refresh_token = create_refresh_token(user.user_id)
        db.query(user_refresh_token_table).filter(
            user_refresh_token_table.user_id == user.user_id
        ).update({
            "refresh_token": re_refresh_token,
            "ip_address": request.client.host,
            "user_agent": user_agent,
            "device_name": device_name,
            "expires_at": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "is_revoked": False
        })
        db.commit()
        return {
            "success": True,
            "message": "Login successful",
            "role": access_record.role,
            "access_token": create_access_token(user.user_id, access_record.role),
            "refresh_token": re_refresh_token
        }
    
    async def forget_password_token_email(self, data, db: Session):
        result = (
            db.query(user_profile_table, user_access_table)
            .join(
                user_access_table,
                user_access_table.user_id == user_profile_table.user_id
            )
            .filter(
                user_profile_table.user_email == data.email,
                user_profile_table.user_email_verified == True
            )
            .first()
        )

        if not result:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        user, access_record = result

        if not user or access_record.role == "Admin":
            raise HTTPException(status_code=400, detail="User or trainer with this email does not exist")

        forget_token = create_forget_token(user.user_id, "user")
        subject = "Gyanteerth Password Reset Code"
        body = forget_password_email_template(forget_token)
        # Sending email directly (await) instead of background task
        # so it works reliably on free-tier deployments
        await send_email(data.email, subject, body)
        return {
            "success": True,
            "message": "Password reset token sent to your email"
        }
    
    async def update_password_service(self, data, db: Session):

        token_data = decode_token(data.token)

        if not token_data or token_data.get("type") != "forget":
            raise HTTPException(status_code=401, detail="Invalid forget token")

        user_id = token_data.get("user_id")

        result = (
            db.query(user_profile_table, user_access_table)
            .join(
                user_access_table,
                user_access_table.user_id == user_profile_table.user_id
            )
            .filter(
                user_profile_table.user_id == user_id,
                user_profile_table.user_email_verified == True
            )
            .first()
        )
        if not result:
            raise HTTPException(status_code=400, detail="User not found or email not verified")
        
        user, access_record = result

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if not access_record:
            raise HTTPException(status_code=400, detail="User does not have an email access account")

        access_record.password_hash = hash_password(data.new_password)
        db.commit()

        return {
            "success": True,
            "message": "Password updated successfully"
        }
    
    async def google_signup_service(self, data, db: Session):
        token = data.get("id_token")        
        if not token:
            raise HTTPException(status_code=400, detail="Token missing")        
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID,clock_skew_in_seconds=30
            )        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid Google Token {str(e)}")        
        user_data = {
            "provider": "google",
            "provider_id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "profile_picture": idinfo.get("picture"),
            "email_verified": idinfo.get("email_verified")
        }        
        existing_user = db.query(user_profile_table).filter(
            user_profile_table.user_email == user_data["email"]
        ).first()
        if existing_user and existing_user.user_email_verified:
            check_pass = db.query(user_access_table).filter(
                user_access_table.user_id == existing_user.user_id,
                user_access_table.password_hash != None
            ).first()
            if check_pass:
                access_token = create_access_token(existing_user.user_id, "user")
                refresh_token = create_refresh_token(existing_user.user_id)
                db.query(user_refresh_token_table).filter(
                user_refresh_token_table.user_id == existing_user.user_id
                ).update({
                    "refresh_token": refresh_token,
                    "ip_address": "Google OAuth",
                    "user_agent": "Google OAuth",
                    "device_name": "Google OAuth",
                    "expires_at": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                    "is_revoked": False
                })
                db.commit()
                return {
                    "success": True,
                    "message": "Login successful",
                    "role":check_pass.role,
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            else:
                self.delete_user_profile_service(existing_user.user_id, db)
        new_user = user_profile_table(
            user_id=f"USER-{uuid.uuid4()}",
            user_email=idinfo.get("email"),
            user_name=idinfo.get("name"),
            user_pic=idinfo.get("picture"),
            user_email_verified=True,
            Status = "Active"
        )
        new_access = user_access_table(
            access_id=f"Access-{uuid.uuid4()}",
            user_id=new_user.user_id,
            provider_id= idinfo.get("sub"),
            provider_name="google",
            role="user",
            password_hash = hash_password("google"+new_user.user_id)
        )
        access_token = create_access_token(new_user.user_id, "user")
        refresh_token = create_refresh_token(new_user.user_id)
        new_refresh_token = user_refresh_token_table(
            refresh_token_id=f"RefreshToken-{uuid.uuid4()}",
            user_id=new_user.user_id,
            refresh_token=refresh_token,
            ip_address="Google OAuth",
            user_agent="Google OAuth",
            device_name="Google OAuth",
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False
        )
        db.add(new_user)
        db.flush()   
        
        db.add(new_access)
        db.add(new_refresh_token)
        
        db.commit()
        return {
            "success": True,
            "message": "Signup successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        }