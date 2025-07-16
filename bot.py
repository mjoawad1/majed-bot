import os
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# ====================== CONFIG ======================
TICKER = "LLY"
RSI_PERIOD = 14
INTERVAL = "5m"
LOOKBACK = "7d"
VOLUME_SPIKE_MULTIPLIER = 2
RSI_THRESHOLD = 50
VWAP_DELTA_LIMIT = 0.5
TG_BOT_TOKEN = "7751828513:AAENaClWSgpDl3MWHKKggsrikLNL2UAgIKU"
TG_CHAT_ID = "907017696"
# ====================================================

def get_data():
    df = yf.download(TICKER, period=LOOKBACK, interval=INTERVAL)
    df.dropna(inplace=True)

    df['vwap'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()

    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(RSI_PERIOD).mean()
    avg_loss = pd.Series(loss).rolling(RSI_PERIOD).mean()

    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    return df

def validate_setup(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    conditions = [
        last['Close'] > last['vwap'],
        last['Volume'] > prev['Volume'] * VOLUME_SPIKE_MULTIPLIER,
        last['rsi'] > RSI_THRESHOLD,
        abs(last['Close'] - last['vwap']) < VWAP_DELTA_LIMIT
    ]

    return all(conditions), last

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}

    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print("Starting scanner...")
    while True:
        try:
            df = get_data()
            valid, last = validate_setup(df)

            if valid:
                msg = (
                    f"\U0001F6A8 Alert for {TICKER}\n"
                    f"Price: {last['Close']:.2f}\n"
                    f"Volume: {last['Volume']}\n"
                    f"RSI: {last['rsi']:.2f}\n"
                    f"VWAP: {last['vwap']:.2f}"
                )
                print(msg)
                send_telegram_alert(msg)
            else:
                print(f"{datetime.now()}: No valid setup.")
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(300)  # كل 5 دقائق

if __name__ == "__main__":
    main()
