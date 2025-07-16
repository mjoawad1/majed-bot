# advanced_stock_bot.py

import yfinance as yf
import time
import requests
import pandas as pd
from datetime import datetime

TG_BOT_TOKEN = "7751828513:AAENaClWSgpDl3MWHKKggsrikLNL2UAgIKU"
TG_CHAT_ID = "907017696"

# يتم تحميل الأسهم ذات الزخم بناءً على شروط الفوليوم والفلوت والسعر
# في النسخة الواقعية يجب ربطها مع API خارجي أو ملف CSV محدث باستمرار

def get_filtered_stocks():
    tickers = pd.read_csv("https://www.dropbox.com/scl/fi/zv8k8e9yazuzxw5kq3fvb/us_stocks_data.csv?rlkey=vmp2yirfvc0wd1bxqh3lvgwus&raw=1")
    filtered = tickers[
        (tickers["Volume"] > 5_000_000) &
        (tickers["Float"] < 20_000_000) &
        (tickers["Price"] <= 100)
    ]
    top_100_tech = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMD", "META", "ADBE", "CRM", "INTC", "AVGO"]  # مثال مبسط
    combined = list(set(filtered["Ticker"].tolist() + top_100_tech))
    return combined

def check_signal(ticker):
    try:
        data = yf.download(ticker, interval="15m", period="1d")
        if data is None or len(data) < 20:
            return None

        df = data.copy()
        df["vwap"] = (df["High"] + df["Low"] + df["Close"]) / 3
        df["rsi"] = df["Close"].rolling(window=14).mean()
        df["macd"] = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        volume_spike = last["Volume"] > (prev["Volume"] * 2)
        price_above_vwap = last["Close"] > last["vwap"]
        macd_positive = last["macd"] > 0
        rsi_valid = last["rsi"] > 50

        if volume_spike and price_above_vwap and macd_positive and rsi_valid:
            return {
                "ticker": ticker,
                "price": last["Close"],
                "volume": last["Volume"],
                "rsi": last["rsi"],
                "vwap": last["vwap"],
                "macd": last["macd"]
            }
        return None

    except Exception as e:
        print(f"Error with {ticker}: {e}")
        return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

def run_bot():
    while True:
        print(f"\n[SCAN] Running scan at {datetime.now().strftime('%H:%M:%S')}")
        STOCK_LIST = get_filtered_stocks()
        signals = []

        for ticker in STOCK_LIST:
            signal = check_signal(ticker)
            if signal:
                signals.append(signal)

        if signals:
            for s in signals:
                msg = (
                    f"🌟 SIGNAL DETECTED: {s['ticker']}\n"
                    f"Price: ${s['price']:.2f}\n"
                    f"Volume: {int(s['volume']):,}\n"
                    f"RSI: {s['rsi']:.2f}\n"
                    f"VWAP: {s['vwap']:.2f}\n"
                    f"MACD: {s['macd']:.2f}"
                )
                send_telegram(msg)
        else:
            print("No valid signals at this cycle.")

        time.sleep(600)  # كل 10 دقائق

if __name__ == "__main__":
    run_bot()
