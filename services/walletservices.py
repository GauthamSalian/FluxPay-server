import os
import random
from dotenv import load_dotenv
from db import supabase
from twilio.rest import Client
# reuse hash logic from userservices to hash userpin
from services import userservices

load_dotenv()

wallet_otp_store = {}

def send_wallet_otp(phone_number: str):
    if not phone_number:
        raise ValueError("Phone number is required to send OTP")
        
    otp = str(random.randint(100000, 999999))
    try:
        account_sid = os.getenv("TWILIO_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        client = Client(account_sid, auth_token)
        
        client.messages.create(
            body=f"Ur fluxpay wallet creation otp is {otp}",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone_number
        )
    except Exception as e:
        raise ValueError(f"Failed to send OTP via Twilio: {str(e)}")
        
    wallet_otp_store[phone_number] = otp
    return True

def create_wallet(user_id: str, phone_number: str, user_pin: str, confirm_pin: str, otp: str):
    # 1. Check if wallet already exists
    query = supabase.table("wallet").select("*").eq("user_id", user_id).execute()
    if query.data:
        raise ValueError("Wallet already exists for this user")
        
    # 2. Check pin
    if user_pin != confirm_pin:
        raise ValueError("Pins do not match")
        
    # 3. Verify OTP
    stored_otp = wallet_otp_store.get(phone_number)
    if not stored_otp or stored_otp != otp:
        raise ValueError("Invalid or expired OTP")
        
    # Clean up OTP after verification
    del wallet_otp_store[phone_number]
    
    # 4. Save to db
    hashed_pin = userservices.hash_password(user_pin)
    wallet_data = {
        "user_id": user_id,
        "balance": 0.0,
        "transaction_pin": hashed_pin  # saving hashed pin in payload as requested
    }
    
    response = supabase.table("wallet").insert(wallet_data).execute()
    return response

def get_wallet(user_id: str):
    query = supabase.table("wallet").select("*").eq("user_id", user_id).execute()
    if not query.data:
        raise ValueError("Wallet not found")
    return query.data[0]