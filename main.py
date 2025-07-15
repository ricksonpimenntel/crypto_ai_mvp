import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Example route (can be replaced with your AI prediction logic)
@app.route('/')
def home():
    return '✅ CryptoOracle Flask backend is running!'

# Prediction endpoint example (replace with your real logic)
@app.route('/predict')
def predict():
    coin = request.args.get('coin')
    if not coin:
        return jsonify({'error': 'Missing coin parameter'}), 400

    # Dummy response (replace with your actual model or logic)
    dummy_result = {
        'rsi': 42.5,
        'coin': coin,
        'chartData': [
            {'x': 1, 'y': 43.2},
            {'x': 2, 'y': 42.9},
            {'x': 3, 'y': 42.5}
        ]
    }
    return jsonify(dummy_result)

# Run on the correct host/port for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
