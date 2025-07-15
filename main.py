from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get('ALPHA_VANTAGE_KEY')

# Coin mapping for Alpha Vantage symbols
COIN_MAP = {
    'btc': 'BTC',
    'eth': 'ETH',
    'xrp': 'XRP',
    'sol': 'SOL',
    'ada': 'ADA'
}

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

@app.route('/predict', methods=['GET'])
def predict():
    coin = request.args.get('coin', '').upper()
    symbol = COIN_MAP.get(coin.lower())
    if not symbol:
        return jsonify({'error': f'Coin não suportado: {coin}'}), 400

    try:
        url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market=USD&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('Time Series (Digital Currency Daily)', {})
        if not data:
            return jsonify({'error': 'No data available'}), 500

        # Take last 15 days' close prices
        dates = sorted(data.keys())[-15:]
        closes = [float(data[date]['4. close']) for date in dates]
        df = pd.DataFrame(closes, columns=['close'])
        rsi = calculate_rsi(df['close'])

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)