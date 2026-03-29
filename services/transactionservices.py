import uuid
from datetime import datetime, timezone
from db import supabase
from services import walletservices, userservices

def get_transaction_history(user_id: str):
    wallet = walletservices.get_wallet(user_id)
    wallet_id = str(wallet["id"])
    
    # Fetch transactions with nested user information for both sender and receiver
    query = supabase.table("transactions") \
        .select("*, sender:sender_wallet_id(id, user:user_id(username)), receiver:receiver_wallet_id(id, user:user_id(username))") \
        .or_(f"sender_wallet_id.eq.{wallet_id},receiver_wallet_id.eq.{wallet_id}") \
        .order("created_at", desc=True) \
        .execute()
    
    # Flatten the response for easier frontend consumption
    transactions = []
    for tx in query.data:
        tx_copy = tx.copy()
        try:
            tx_copy["sender_name"] = tx.get("sender", {}).get("user", {}).get("username", "Unknown")
            tx_copy["receiver_name"] = tx.get("receiver", {}).get("user", {}).get("username", "Unknown")
        except:
            tx_copy["sender_name"] = "Unknown"
            tx_copy["receiver_name"] = "Unknown"
        transactions.append(tx_copy)
        
    return transactions

def process_transaction(sender_id: str, receiver_id: str, amount: float, pin: str, location: str = "Unknown", label: str = "miscellaneous"):
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
    
    # Update balances
    supabase.table("wallet").update({"balance": new_sender_balance}).eq("id", sender_wallet_id["id"]).execute()
    supabase.table("wallet").update({"balance": new_receiver_balance}).eq("id", receiver_wallet_id["id"]).execute()
    
    tx_data = {
        "id": str(uuid.uuid4()),
        "sender_wallet_id": sender_wallet_id["id"],
        "receiver_wallet_id": receiver_wallet_id["id"],
        "amount": amount,
        "location": location,
        "label": label,
        "status": "success", # Since money is transferred from wallet
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = supabase.table("transactions").insert(tx_data).execute()
    return response.data[0] if response.data else tx_data

def transact_by_receiver_phone(user_id: str, receiver_phone: str, amount: float, pin: str, location: str = "Unknown", label: str = "miscellaneous"):
    user_query = supabase.table("users").select("id").eq("phone", receiver_phone).execute()
    if not user_query.data:
        raise ValueError("Receiver not found by this phone number")
    receiver_id = str(user_query.data[0]["id"])
    return process_transaction(user_id, receiver_id, amount, pin, location, label)

def transact_by_receiver_mail(user_id: str, receiver_email: str, amount: float, pin: str, location: str = "Unknown", label: str = "miscellaneous"):
    user_query = supabase.table("users").select("id").eq("email", receiver_email).execute()
    if not user_query.data:
        raise ValueError("Receiver not found by this email address")
    receiver_id = str(user_query.data[0]["id"])
    return process_transaction(user_id, receiver_id, amount, pin, location, label)

def get_name_by_phone(phone: str):
    user_query = supabase.table("users").select("username").eq("phone", phone).execute()
    if not user_query.data:
        raise ValueError("User not found")
    return user_query.data[0]["username"]

def get_name_by_wallet_id(wallet_id: str):
    # wallet_id -> user_id -> username
    query = supabase.table("wallet").select("user_id(username)").eq("id", wallet_id).execute()
    if not query.data:
        raise ValueError("Wallet not found")
    return query.data[0].get("user_id", {}).get("username", "Unknown")

def transact_by_receiver_wallet(user_id: str, receiver_wallet_id: str, amount: float, pin: str, location: str = "Unknown", label: str = "miscellaneous"):
    # First, get the user_id associated with this wallet_id
    query = supabase.table("wallet").select("user_id").eq("id", receiver_wallet_id).execute()
    if not query.data:
        raise ValueError("Receiver wallet not found")
    receiver_id = str(query.data[0]["user_id"])
    return process_transaction(user_id, receiver_id, amount, pin, location, label)
