#DONT RUN THIS SCRIPT 

import os
import random
import hashlib
from datetime import datetime, timezone
from db import supabase

# Dummy data generator
def hash_password(password: str) -> str:
    # Optional dummy hash if bcrypt is not yet set up
    # Can be replaced with actual hashing (Passlib, Bcrypt, etc.) later
    return hashlib.sha256(password.encode()).hexdigest()

users_data = [
    {
        "email": "alice@fluxpay.com",
        "phone": "+1234567890",
        "password": "Password123!",
        "location": "New York, USA"
    },
    {
        "email": "bob@fluxpay.com",
        "phone": "+0987654321",
        "password": "Password123!",
        "location": "London, UK"
    },
    {
        "email": "charlie@fluxpay.com",
        "phone": "+1122334455",
        "password": "Password123!",
        "location": "Sydney, AU"
    }
]

def seed_db():
    print("Starting database seed...")
    try:
        # 1. Seed Users
        print("\nSeeding users...")
        inserted_users = []
        for u in users_data:
            user_payload = {
                "email": u["email"],
                "phone": u["phone"],
                "hashed_password": hash_password(u["password"]),
                "location": u["location"],
                "last_verified_at": datetime.now(timezone.utc).isoformat()
            }
            res = supabase.table("users").insert(user_payload).execute()
            inserted_user = res.data[0]
            inserted_users.append(inserted_user)
            print(f"Created User: {u['email']} | Password: {u['password']}")

        # 2. Seed Wallets
        print("\nSeeding wallets...")
        inserted_wallets = []
        for i, user in enumerate(inserted_users):
            wallet_payload = {
                "user_id": user["id"],
                "balance": random.randint(1000, 5000), # random balance between 1000 and 5000
                "transaction_pin": "1234" # Dummy pin
            }
            res = supabase.table("wallet").insert(wallet_payload).execute()
            inserted_wallets.append(res.data[0])
            print(f"Created Wallet for User: {user['email']} with Balance: {wallet_payload['balance']} and PIN: {wallet_payload['transaction_pin']}")

        # 3. Seed Deposits
        print("\nSeeding deposits...")
        for wallet in inserted_wallets:
            deposit_payload = {
                "wallet_id": wallet["id"],
                "amount": random.randint(100, 500)
            }
            supabase.table("deposits").insert(deposit_payload).execute()
        print("Created Deposits for all wallets.")

        # 4. Seed Loans
        print("\nSeeding loans...")
        loan_payload = {
            "giver_wallet_id": inserted_wallets[0]["id"], # Alice
            "receiver_wallet_id": inserted_wallets[1]["id"], # Bob
            "amount": 500,
            "remaining_amount": 500,
            "last_paid_at": datetime.now(timezone.utc).isoformat()
        }
        loan_res = supabase.table("loans").insert(loan_payload).execute()
        loan = loan_res.data[0]
        print("Created Loan: Alice (Giver) -> Bob (Receiver) for Amount: 500")

        # 5. Seed Transactions
        print("\nSeeding transactions...")
        transaction_payloads = [
            {
                "sender_wallet_id": inserted_wallets[1]["id"], # Bob
                "receiver_wallet_id": inserted_wallets[0]["id"], # Alice
                "amount": 100,
                "location": "Online",
                "label": "food",
                "status": "success",
                "loan_id": None
            },
            {
                "sender_wallet_id": inserted_wallets[0]["id"], # Alice
                "receiver_wallet_id": inserted_wallets[2]["id"], # Charlie
                "amount": 200,
                "location": "Store",
                "label": "miscellaneous",
                "status": "pending",
                "loan_id": None
            },
            {
                "sender_wallet_id": inserted_wallets[2]["id"], # Charlie
                "receiver_wallet_id": inserted_wallets[1]["id"], # Bob
                "amount": 1500,
                "location": "Suspicious Location",
                "label": "loan",
                "status": "blocked",
                "loan_id": loan["id"]
            }
        ]
        
        inserted_transactions = []
        for txn in transaction_payloads:
            res = supabase.table("transactions").insert(txn).execute()
            inserted_transactions.append(res.data[0])
            print(f"Created Transaction: {txn['amount']} ({txn['label']}) | Status: {txn['status']}")

        # 6. Seed Risk Logs
        print("\nSeeding risk logs...")
        blocked_txn = next(t for t in inserted_transactions if t["status"] == "blocked")
        risk_log_payload = {
            "transaction_id": blocked_txn["id"],
            "risk_score": 85.5,
            "reason": "High amount transaction from suspicious location."
        }
        supabase.table("risk_logs").insert(risk_log_payload).execute()
        print("Created Risk Log for blocked transaction.")

        print("\n==========================================")
        print("             SEEDING COMPLETE             ")
        print("==========================================")
        print("You can use these credentials to log in:")
        print("------------------------------------------")
        for u in users_data:
            print(f"Email: {u['email']}")
            print(f"Password: {u['password']}")
            print("------------------------------------------")
        
        print("\nThe explicit Wallet Transaction PIN for all seeded users is: 1234")
        print("==========================================")

    except Exception as e:
        print(f"An error occurred during seeding script execution: {e}")

if __name__ == "__main__":
    seed_db()
