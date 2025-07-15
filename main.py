from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/predict", methods=["GET"])
def predict():
    coin = request.args.get("coin")
    try:
        yf_symbol = coin.replace("/", "-")
        df = yf.download(tickers=yf_symbol, period="7d", interval="1h")

        if df.empty:
            return jsonify({"error": "No data available from Yahoo Finance"})

        close_prices = df["Close"]
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.iloc[-1]

        recommendation = (
            "BUY" if latest_rsi < 30 else "SELL" if latest_rsi > 70 else "HOLD"
        )

        return jsonify({
            "coin": coin,
            "rsi": round(latest_rsi, 2),
            "recommendation": recommendation
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
