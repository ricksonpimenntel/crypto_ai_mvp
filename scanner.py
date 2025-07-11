import ccxt
import pandas as pd
import ta

exchange = ccxt.binance()

def fetch_ohlcv(symbol='BTC/USDT', timeframe='1h', limit=100):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def analyze_ta(df):
    rsi = ta.momentum.RSIIndicator(df['close']).rsi()
    macd = ta.trend.MACD(df['close'])
    return {
        'RSI': rsi.iloc[-1],
        'MACD': macd.macd().iloc[-1],
        'Signal': macd.macd_signal().iloc[-1],
    }

def signal_from_rsi(rsi):
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    else:
        return "NEUTRAL"

if __name__ == '__main__':
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT', 'LINK/USDT']

    for coin in coins:
        print(f"📊 Analyzing {coin}...")
        df = fetch_ohlcv(coin)
        analysis = analyze_ta(df)
        signal = signal_from_rsi(analysis['RSI'])
        print(f"RSI: {analysis['RSI']:.2f}")
        print(f"MACD: {analysis['MACD']:.4f}")
        print(f"Signal Line: {analysis['Signal']:.4f}")
        print(f"Signal: {signal}\n")
