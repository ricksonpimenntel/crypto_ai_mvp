from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Coin mapping for Yahoo Finance symbols
COIN_MAP = {
    'btc': 'BTC-USD',
    'eth': 'ETH-USD',
    'xrp': 'XRP-USD',
    'sol': 'SOL-USD',
    'ada': 'ADA-USD'
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
    coin = request.args.get('coin', '').lower()
    symbol = COIN_MAP.get(coin)
    if not symbol:
        return jsonify({'error': f'Coin não suportado: {coin.upper()}'}), 400

    try:
        # Calculate timestamps for last 15 days
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=15)).timestamp())
        url = f"https://finance.yahoo.com/quote/{symbol}/history?period1={start_time}&period2={end_time}&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Extract JSON from HTML (Yahoo embeds it in HistoricalPriceStore)
        if "HistoricalPriceStore" not in response.text:
            return jsonify({'error': 'No historical data found in response'}), 500

        start = response.text.find('HistoricalPriceStore":{"prices":') + 31
        end = response.text.find(',"isPending"', start)
        json_str = response.text[start:end]
        data = pd.read_json(json_str)
        data = data.sort_values('date', ascending=True)  # Sort by date
        closes = data['close'].dropna()
        if len(closes) < 15:
            return jsonify({'error': 'Insufficient data for RSI'}), 500

        rsi = calculate_rsi(closes[-15:])  # Last 15 closes

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)