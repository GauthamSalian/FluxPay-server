import bcrypt
from datetime import datetime, timezone
from db import supabase

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
    return response

def login_user(email: str = None, phone: str = None, password: str = None):
    if not password:
        raise ValueError("Password is required")
    if not email and not phone:
        raise ValueError("Email or phone is required")
        
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
