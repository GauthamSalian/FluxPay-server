from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import walletservices
from services.userservices import get_current_user

router = APIRouter()

class CreateWalletReq(BaseModel):
    user_pin: str
    confirm_pin: str
    otp: str

@router.post("/send-otp")
def send_wallet_otp_route(current_user: dict = Depends(get_current_user)):
    try:
        phone = current_user.get("phone")
        if not phone:
            raise ValueError("Phone number is required, but missing from user profile")
        walletservices.send_wallet_otp(phone)
        return {"message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create")
def create_wallet_route(req: CreateWalletReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("id"))
        phone = current_user.get("phone")
        response = walletservices.create_wallet(
            user_id=user_id,
            phone_number=phone,
            user_pin=req.user_pin,
            confirm_pin=req.confirm_pin,
            otp=req.otp
        )
        return {"message": "Wallet created successfully", "data": response.data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_user_wallet_route(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("id"))
        wallet = walletservices.get_wallet(user_id=user_id)
        # Avoid returning the hashed pin payload to frontend if not necessary
        safe_wallet = {k: v for k, v in wallet.items() if k != "transaction_pin"}
        return {"message": "Wallet found", "wallet": safe_wallet}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

import os

class DepositOrderReq(BaseModel):
    amount: float

class VerifyDepositReq(BaseModel):
    amount: float
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@router.post("/deposit/order")
def deposit_order_route(req: DepositOrderReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("id"))
        order = walletservices.create_deposit_order(user_id=user_id, amount=req.amount)
        return {
            "order": order,
            "key": os.getenv("RAZORPAY_TEST_ID") # Return the public key to the frontend dynamically
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deposit/verify")
def deposit_verify_route(req: VerifyDepositReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("id"))
        result = walletservices.deposit_funds_to_wallet(
            user_id=user_id, 
            amount=req.amount,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_order_id=req.razorpay_order_id,
            razorpay_signature=req.razorpay_signature
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
