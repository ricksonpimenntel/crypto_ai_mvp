from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
from io import StringIO

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
    coin = request.args.get('coin', '').upper()
    symbol = COIN_MAP.get(coin.lower())
    if not symbol:
        return jsonify({'error': f'Coin não suportado: {coin}'}), 400

    try:
        # Fetch last 15 days of daily prices from Yahoo Finance (CSV format)
        url = f"https://finance.yahoo.com/quote/{symbol}/history?p={symbol}&period1={int(pd.Timestamp.now() - pd.Timedelta(days=15).timestamp())}&period2={int(pd.Timestamp.now().timestamp())}&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true"
        headers = {'User-Agent': 'Mozilla/5.0'}  # Mimic browser to avoid block
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # Parse the CSV data from the response (Yahoo returns HTML with embedded CSV)
        # Note: This is unofficial, but reliable for MVP
        csv_data = response.text.split('HistoricalPriceStore": {"prices" :')[1].split(',"isPending"')[0]
        df = pd.read_json(StringIO(csv_data))
        df = df.sort_values('date')  # Sort by date
        closes = df['close'].dropna()
        if len(closes) < 15:
            return jsonify({'error': 'Insufficient data for RSI'}), 500

        rsi = calculate_rsi(closes[-15:])  # Last 15 closes for RSI

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)