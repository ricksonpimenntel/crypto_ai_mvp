import yfinance as yf
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ta.momentum import RSIIndicator

app = FastAPI()

# Allow CORS from anywhere (for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict")
def predict(coin: str):
    try:
        yf_symbol = coin.replace("/", "-")
        df = yf.download(tickers=yf_symbol, period="7d", interval="1h")

        if df.empty:
            return {"error": "No data available from Yahoo Finance"}

        rsi = RSIIndicator(close=df["Close"]).rsi().iloc[-1]

        return {
            "coin": coin,
            "rsi": round(rsi, 2),
            "recommendation": (
                "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD"
            )
        }

    except Exception as e:
        return {"error": str(e)}
