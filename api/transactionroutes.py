from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import transactionservices
from services.userservices import get_current_user

router = APIRouter()

class TransactPhoneReq(BaseModel):
    receiver_phone: str
    amount: float
    pin: str
    location: str = "Unknown"
    label: str = "miscellaneous"

class TransactMailReq(BaseModel):
    receiver_email: str
    amount: float
    pin: str
    location: str = "Unknown"
    label: str = "miscellaneous"

class TransactWalletReq(BaseModel):
    receiver_wallet_id: str
    amount: float
    pin: str
    location: str = "Unknown"
    label: str = "miscellaneous"

@router.get("/history")
def get_transaction_history_route(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        history = transactionservices.get_transaction_history(user_id)
        return {"transactions": history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify/phone/{phone}")
def verify_phone_route(phone: str, current_user: dict = Depends(get_current_user)):
    try:
        name = transactionservices.get_name_by_phone(phone)
        return {"name": name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify/wallet/{wallet_id}")
def verify_wallet_route(wallet_id: str, current_user: dict = Depends(get_current_user)):
    try:
        name = transactionservices.get_name_by_wallet_id(wallet_id)
        return {"name": name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
            pin=req.pin,
            location=req.location,
            label=req.label
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
            pin=req.pin,
            location=req.location,
            label=req.label
        )
        return {"message": "Transaction successful", "transaction": tx}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send/wallet")
def send_by_wallet_route(req: TransactWalletReq, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        tx = transactionservices.transact_by_receiver_wallet(
            user_id=user_id, 
            receiver_wallet_id=req.receiver_wallet_id, 
            amount=req.amount, 
            pin=req.pin,
            location=req.location,
            label=req.label
        )
        return {"message": "Transaction successful", "transaction": tx}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
