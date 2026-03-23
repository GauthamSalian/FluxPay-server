from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.userroutes import router as user_router
from api.walletroutes import router as wallet_router
from api.transactionroutes import router as transaction_router

app = FastAPI(title="FluxPay Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(wallet_router, prefix="/api/wallets", tags=["wallets"])
app.include_router(transaction_router, prefix="/api/transactions", tags=["transactions"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FluxPay Server"}
