from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import ccxt
import pandas as pd
import ta

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict")
def predict(coin: str = Query(..., description="Coin pair like SOL/USDT")):
    exchange = ccxt.binance()
    symbol = coin.upper()
    try:
        # Fetch OHLCV data (open, high, low, close, volume)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Add technical indicators
        df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        # Fill NaNs and prepare latest signal
        df = df.fillna(method='bfill')

        latest = df.iloc[-1]
        rec = "NEUTRAL"
        if latest['RSI'] > 70:
            rec = "SELL"
        elif latest['RSI'] < 30:
            rec = "BUY"

        # Prepare chart data (return last 25 entries)
        chart = df.tail(25)[['timestamp', 'close', 'RSI', 'MACD']].copy()
        chart['timestamp'] = chart['timestamp'].astype(str)
        chart_data = chart.to_dict(orient="records")

        return {
            "coin": symbol,
            "RSI": round(latest['RSI'], 2),
            "MACD": round(latest['MACD'], 4),
            "SignalLine": round(latest['Signal'], 4),
            "Recommendation": rec,
            "chartData": chart_data
        }

    except Exception as e:
        return {"error": str(e)}

