from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
import numpy as np
import statsmodels.api as sm
from datetime import datetime
from scanner import fetch_ohlcv, analyze_ta, signal_from_rsi

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Função para calcular RSI (período 14)
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Função para calcular MACD (EMA12 - EMA26, signal=EMA9)
def calculate_macd(data, short=12, long=26, signal=9):
    ema_short = data['close'].ewm(span=short, adjust=False).mean()
    ema_long = data['close'].ewm(span=long, adjust=False).mean()
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

# Função para regressão linear e previsão
def linear_regression_prediction(df):
    df['day'] = np.arange(len(df))  # Dias sequenciais
    X = sm.add_constant(df['day'])  # Adiciona intercepto
    y = df['close']
    model = sm.OLS(y, X).fit()
    next_day = df['day'].max() + 1
    predicted_price = model.predict([[1, next_day]])[0]
    return predicted_price

# Mapeamento de coins para CoinGecko
coin_map = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "SOL/USDT": "solana",
}

@app.get("/predict")
async def predict(coin: str = Query(..., description="Coin pair like SOL/USDT")):
    try:
        coin_id = coin_map.get(coin.upper(), None)
        if not coin_id:
            raise ValueError(f"Coin não suportado: {coin}.")

        # Coleta dados (30 dias, diários)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30&interval=daily"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Erro na API da CoinGecko")

        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Indicadores
        df['RSI'] = calculate_rsi(df)
        df['MACD'], df['signal'] = calculate_macd(df)

        df = df.dropna()

        if df.empty:
            raise ValueError("Dados insuficientes")

        latest = df.iloc[-1]
        current_price = latest['close']

        # Previsão com regressão linear
        predicted_price = linear_regression_prediction(df)

        # Lucro potencial (%)
        potential_profit = ((predicted_price - current_price) / current_price) * 100

        # Recomendação combinada (RSI + previsão)
        rsi_rec = "BUY" if latest['RSI'] < 30 else "SELL" if latest['RSI'] > 70 else "HOLD"
        pred_rec = "BUY" if potential_profit > 1 else "SELL" if potential_profit < -1 else "HOLD"
        recommendation = pred_rec if pred_rec != "HOLD" else rsi_rec  # Prioriza previsão se forte

        # Chart data (últimos 25)
        chart_df = df.tail(25)[['timestamp', 'close', 'RSI', 'MACD', 'signal']].copy()
        chart_df['timestamp'] = chart_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        chart_data = chart_df.to_dict(orient='records')

        return {
            "symbol": coin,
            "RSI": round(latest['RSI'], 2),
            "MACD": round(latest['MACD'], 2),
            "signal": round(latest['signal'], 2),
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "potential_profit": round(potential_profit, 2),
            "recommendation": recommendation,
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/scan")
async def scan():
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT', 'LINK/USDT', 'XRP/USDT']
    results = []
    for coin in coins:
        try:
            df = fetch_ohlcv(coin)
            analysis = analyze_ta(df)
            signal = signal_from_rsi(analysis['RSI'])
            results.append({
                'symbol': coin,
                'RSI': round(analysis['RSI'], 2),
                'MACD': round(analysis['MACD'], 4),
                'signal': round(analysis['Signal'], 4),
                'recommendation': signal
            })
        except Exception as e:
            results.append({'symbol': coin, 'error': str(e)})
    return {'scan_results': results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)