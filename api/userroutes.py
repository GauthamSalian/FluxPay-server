from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import userservices

router = APIRouter()

class CreateUserReq(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    location: str

class LoginUserReq(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str

class ChangePasswordReq(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    old_password: str
    new_password: str
    confirm_new_password: str

@router.post("/create-user")
def create_user_route(req: CreateUserReq):
    try:
        response = userservices.create_user(
            name=req.name,
            email=req.email,
            phone=req.phone,
            password=req.password,
            location=req.location
        )
        return {"message": "User created successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SendOtpReq(BaseModel):
    email: str

class VerifyOtpReq(BaseModel):
    email: str
    otp: str

@router.post("/send-otp")
def send_otp_route(req: SendOtpReq):
    try:
        otp = userservices.generate_otp()
        userservices.send_otp_email(req.email, otp)
        return {"message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp")
def verify(req: VerifyOtpReq):
    if userservices.verify_otp(req.email, req.otp):
        return {"message": "Verified"}
    return {"message": "Invalid OTP"}

class SendOtpSmsReq(BaseModel):
    phone: str

class VerifyOtpSmsReq(BaseModel):
    phone: str
    otp: str

@router.post("/send-otp-sms")
def send_otp_sms_route(req: SendOtpSmsReq):
    try:
        otp = userservices.generate_otp()
        userservices.send_otp_sms(req.phone, otp)
        return {"message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp-sms")
def verify_sms(req: VerifyOtpSmsReq):
    if userservices.verify_otp_sms(req.phone, req.otp):
        return {"message": "Verified"}
    return {"message": "Invalid OTP"}

@router.post("/login")
def login_user_route(req: LoginUserReq):
    try:
        user = userservices.login_user(
            email=req.email,
            phone=req.phone,
            password=req.password
        )
        # Avoid returning the hashed password
        safe_user_data = {k: v for k, v in user.items() if k != "hashed_password"}
        return {"message": "Login successful", "user": safe_user_data}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
def change_password_route(req: ChangePasswordReq):
    try:
        userservices.change_password(
            email=req.email,
            phone=req.phone,
            old_password=req.old_password,
            new_password=req.new_password,
            confirm_new_password=req.confirm_new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
