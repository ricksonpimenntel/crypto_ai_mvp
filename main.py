from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd

app = Flask(__name__)
CORS(app)

# Coin mapping to CoinGecko IDs
COIN_MAP = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'xrp': 'ripple',
    'sol': 'solana',
    'ada': 'cardano'
}

def calculate_rsi(prices, period=14):
    # Simple RSI without TA-Lib
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

@app.route('/predict', methods=['GET'])
def predict():
    coin = request.args.get('coin', '').lower()
    coin_id = COIN_MAP.get(coin)
    if not coin_id:
        return jsonify({'error': f'Coin não suportado: {coin.upper()}'}), 400

    try:
        # Fetch hourly prices for last 1 day (24 hours, enough for RSI=14)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1&interval=hourly"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        prices = data.get('prices', [])
        if len(prices) < 15:  # Need at least 15 for RSI=14
            return jsonify({'error': 'Insufficient data for RSI'}), 500

        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        rsi = calculate_rsi(df['price'])

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error: {str(e)}")  # For logs
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)