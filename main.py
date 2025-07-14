from flask import Flask, request, jsonify
import requests
import pandas as pd
import ta  # Assume you have TA-Lib installed; if not, use a simple RSI calc

app = Flask(__name__)

# Mapping for common coins to CoinGecko IDs (add more if needed)
COIN_MAP = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'xrp': 'ripple',
    'sol': 'solana',
    'ada': 'cardano'
}

@app.route('/predict', methods=['GET'])
def predict():
    coin = request.args.get('coin', '').lower()  # Convert to lowercase
    coin_id = COIN_MAP.get(coin)
    if not coin_id:
        return jsonify({'error': f'Coin não suportado: {coin.upper()}'}), 400  # Return 400 error for unsupported

    try:
        # Fetch 14 days of prices from CoinGecko (free API, no key needed)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=14&interval=daily"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data.get('prices'):
            return jsonify({'error': 'No data available'}), 500

        # Calculate RSI using TA-Lib (period 14 default)
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        rsi_series = ta.momentum.RSIIndicator(prices['price']).rsi()
        rsi = rsi_series.iloc[-1]  # Latest RSI value

        return jsonify({'rsi': round(rsi, 2)})  # Return rounded for cleanliness
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)  # Render expects port 8080 or env var