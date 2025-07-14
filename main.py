from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/predict', methods=['GET'])
def predict():
    coin = request.args.get('coin', '').upper()  # Uppercase for Binance symbols like BTCUSDT
    symbol = f"{coin}USDT" if 'USDT' not in coin else coin  # Ensure BTC -> BTCUSDT

    try:
        # Fetch 15 daily klines from Binance (last 15 days for RSI=14)
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=15"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            return jsonify({'error': 'No data available'}), 500

        # Extract close prices (index 4 in kline array)
        closes = [float(kline[4]) for kline in data]
        df = pd.DataFrame(closes, columns=['close'])

        # Simple RSI calculation
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

        if rsi_value is None:
            return jsonify({'error': 'Insufficient data for RSI'}), 500

        return jsonify({'rsi': round(rsi_value, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")  # For logs
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)