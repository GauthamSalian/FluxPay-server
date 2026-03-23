import uuid
from datetime import datetime, timezone
from db import supabase
from services import walletservices, userservices

def get_transaction_history(user_id: str):
    wallet = walletservices.get_wallet(user_id)
    wallet_id = str(wallet["id"])
    
    query = supabase.table("transactions").select("*").or_(f"sender_wallet_id.eq.{wallet_id},receiver_wallet_id.eq.{wallet_id}").order("created_at", desc=True).execute()
    return query.data

def process_transaction(sender_id: str, receiver_id: str, amount: float, pin: str):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
        
    if sender_id == receiver_id:
        raise ValueError("Cannot send money to yourself")
        
    sender_wallet_id = walletservices.get_wallet(sender_id)
    try:
        receiver_wallet_id = walletservices.get_wallet(receiver_id)
    except ValueError:
        raise ValueError("Receiver does not have a wallet set up")
    
    if not sender_wallet_id.get("transaction_pin"):
        raise ValueError("Sender wallet has no transaction PIN set")
        
    if not userservices.verify_password(pin, sender_wallet_id["transaction_pin"]):
        raise ValueError("Invalid transaction PIN")
        
    if float(sender_wallet_id["balance"]) < amount:
        raise ValueError("Insufficient funds")
        
    new_sender_balance = float(sender_wallet_id["balance"]) - amount
    new_receiver_balance = float(receiver_wallet_id["balance"]) + amount
    
    supabase.table("wallet").update({"balance": new_sender_balance}).eq("id", sender_wallet_id["id"]).execute()
    supabase.table("wallet").update({"balance": new_receiver_balance}).eq("id", receiver_wallet_id["id"]).execute()
    
    tx_data = {
        "id": str(uuid.uuid4()),
        "sender_wallet_id": sender_wallet_id["id"],
        "receiver_wallet_id": receiver_wallet_id["id"],
        "amount": amount,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = supabase.table("transactions").insert(tx_data).execute()
    return response.data[0] if response.data else tx_data

def transact_by_receiver_phone(user_id: str, receiver_phone: str, amount: float, pin: str):
    user_query = supabase.table("users").select("id").eq("phone", receiver_phone).execute()
    if not user_query.data:
        raise ValueError("Receiver not found by this phone number")
    receiver_id = str(user_query.data[0]["id"])
    return process_transaction(user_id, receiver_id, amount, pin)

def transact_by_receiver_mail(user_id: str, receiver_email: str, amount: float, pin: str):
    user_query = supabase.table("users").select("id").eq("email", receiver_email).execute()
    if not user_query.data:
        raise ValueError("Receiver not found by this email address")
    receiver_id = str(user_query.data[0]["id"])
    return process_transaction(user_id, receiver_id, amount, pin)
