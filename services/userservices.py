import bcrypt
from datetime import datetime, timezone
from db import supabase
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from twilio.rest import Client
from jose import jwt
from datetime import datetime, timedelta
load_dotenv()

otp_store = {}
otp_sms_store = {}
verified_emails = set()
verified_phone_numbers = set()


def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email, otp):
    sender_email = os.getenv("APP_GMAIL")
    app_password = os.getenv("APP_PASSWORD")

    query = supabase.table("users").select("*")
    if receiver_email:
        query = query.eq("email", receiver_email)
        response = query.execute()
        if response.data:
            raise ValueError("Email already exists in the database")

    subject = "FluxPay: Your OTP Code"
    body = f"Your OTP is: {otp}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
    
    otp_store[receiver_email] = str(otp)
    return True

def send_otp_sms(phone_number: str, otp: str):
    query = supabase.table("users").select("*")
    if phone_number:
        query = query.eq("phone", phone_number)
        response = query.execute()
        if response.data:
            raise ValueError("Phone Number already exists in the database")
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"Your OTP is: {otp}. It will expire in 5 minutes.",
        from_= os.getenv("TWILIO_PHONE_NUMBER"),
        to=phone_number
    )

    otp_sms_store[phone_number] = str(otp)
    return True

def verify_otp(email: str, otp: str) -> bool:
    if email not in otp_store:
        return False
    if otp_store[email] != otp:
        return False
    del otp_store[email]
    verified_emails.add(email)
    return True

def verify_otp_sms(phone_number: str, otp: str) -> bool:
    if phone_number not in otp_sms_store:
        return False
    if otp_sms_store[phone_number] != otp:
        return False
    del otp_sms_store[phone_number]
    verified_phone_numbers.add(phone_number)
    return True

def hash_password(password: str) -> str:
    # generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(name: str, email: str, phone: str, password: str, location: str):
    hashed_pw = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()

    if email not in verified_emails:
        raise ValueError("User Email not verified via OTP")

    if phone not in verified_phone_numbers:
        raise ValueError("User Phone Number not verified via OTP")
    
    user_data = {
        "username": name,
        "email": email,
        "phone": phone,
        "hashed_password": hashed_pw,
        "created_at": now,
        "last_verified_at": now,
        "location": location
    }
    
    response = supabase.table("users").insert(user_data).execute()
    
    if email in verified_emails:
        verified_emails.remove(email)
    if phone in verified_phone_numbers:
        verified_phone_numbers.remove(phone)
        
    return response

def login_user(email: str = None, phone: str = None, password: str = None):
    if not password:
        raise ValueError("Password is required")
        
    # Clean up accidental whitespace or empty strings
    email = email.strip() if email and email.strip() else None
    phone = phone.strip() if phone and phone.strip() else None
        
    if not email and not phone:
        raise ValueError("Email or phone is required")
        
    # If the frontend uses a single "Email/Phone" field, it probably sent the phone number as 'email'.
    # We can detect this by checking if the 'email' lacks an '@' symbol.
    if email and "@" not in email:
        if not phone:
            phone = email 
        email = None
        
    query = supabase.table("users").select("*")
    if email:
        query = query.eq("email", email)
    elif phone:
        query = query.eq("phone", phone)
        
    response = query.execute()
    
    if not response.data:
        raise ValueError("User not found")
        
    user = response.data[0]
    if verify_password(password, user["hashed_password"]):
        return user
    else:
        raise ValueError("Invalid credentials")

def change_password(old_password: str, new_password: str, confirm_new_password: str, email: str = None, phone: str = None):
    if new_password != confirm_new_password:
        raise ValueError("New passwords do not match")
        
    # Verify the old credentials first
    user = login_user(email=email, phone=phone, password=old_password)
    
    new_hashed_pw = hash_password(new_password)
    
    update_data = {
        "hashed_password": new_hashed_pw
    }
    
    query = supabase.table("users").update(update_data)
    if email:
        query = query.eq("email", email)
    elif phone:
        query = query.eq("phone", phone)
        
    response = query.execute()
    return response

SECRET_KEY = os.getenv("JWT_SECRET", "your_secret")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=2)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        identifier: str = payload.get("sub")
        if identifier is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    query = supabase.table("users").select("*")
    if "@" in identifier:
        query = query.eq("email", identifier)
    else:
        query = query.eq("phone", identifier)
        
    response = query.execute()
    if not response.data:
        raise credentials_exception
    return response.data[0]