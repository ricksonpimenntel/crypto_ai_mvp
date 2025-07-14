from flask import Flask, request, jsonify
from flask_cors import CORS  # Add if CORS issues, optional
import requests
import pandas as pd
import ta  # For RSI; ensure 'ta-lib' is in requirements.txt

app = Flask(__name__)
CORS(app)  # Enables CORS for frontend requests, optional but good for MVP

# Coin mapping to CoinGecko IDs
COIN_MAP = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'xrp': 'ripple',
    'sol': 'solana',
    'ada': 'cardano'
}

@app.route('/predict', methods=['GET'])
def predict():
    coin = request.args.get('coin', '').lower()
    coin_id = COIN_MAP.get(coin)
    if not coin_id:
        return jsonify({'error': f'Coin não suportado: {coin.upper()}'}), 400

    try:
        # Fetch 14 days of daily prices from CoinGecko
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=14&interval=daily"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        prices = data.get('prices', [])
        if not prices:
            return jsonify({'error': 'No data available for this coin'}), 500

        # Calculate RSI
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        rsi = ta.momentum.RSIIndicator(df['price']).rsi().iloc[-1]

        return jsonify({'rsi': round(rsi, 2)})
    except Exception as e:
        print(f"Error calculating RSI for {coin}: {str(e)}")  # Logs for Render
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)  # Render uses port from env, but set default