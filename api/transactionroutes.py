from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import transactionservices
from services.userservices import get_current_user

router = APIRouter()

class TransactPhoneReq(BaseModel):
    receiver_phone: str
    amount: float
    pin: str

class TransactMailReq(BaseModel):
    receiver_email: str
    amount: float
    pin: str

@router.get("/history")
def get_transaction_history_route(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        history = transactionservices.get_transaction_history(user_id)
        return {"transactions": history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send/phone")
def send_by_phone_route(req: TransactPhoneReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        tx = transactionservices.transact_by_receiver_phone(
            user_id=user_id, 
            receiver_phone=req.receiver_phone, 
            amount=req.amount, 
            pin=req.pin
        )
        return {"message": "Transaction successful", "transaction": tx}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send/email")
def send_by_email_route(req: TransactMailReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        tx = transactionservices.transact_by_receiver_mail(
            user_id=user_id, 
            receiver_email=req.receiver_email, 
            amount=req.amount, 
            pin=req.pin
        )
        return {"message": "Transaction successful", "transaction": tx}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
