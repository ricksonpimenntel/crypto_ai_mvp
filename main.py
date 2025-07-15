from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

# Coin mapping
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
        # Fetch last 15 days daily prices
        data = yf.download(symbol, period='15d', interval='1d')
        if data.empty:
            return jsonify({'error': 'No data available'}), 500

        closes = data['Close'].dropna()
        if len(closes) < 15:
            return jsonify({'error': 'Insufficient data for RSI'}), 500

        rsi = calculate_rsi(closes)

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    