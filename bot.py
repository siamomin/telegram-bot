import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
import talib

# 🔹 Телеграм Бот (замени на свои данные)
TELEGRAM_BOT_TOKEN = '7499296290:AAFJ9uH0Ory3XGk1SuhA9cPfZi104aD1jP8'
TELEGRAM_CHAT_ID = '972103921'

# 🔹 Подключение к MetaTrader 5
mt5.initialize()

# 🔹 Функция для получения данных с MT5
def get_mt5_data(symbol, timeframe, num_candles=100):
    timeframe_dict = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15}
    data = mt5.copy_rates_from_pos(symbol, timeframe_dict[timeframe], 0, num_candles)
    
    if data is None or len(data) == 0:
        print(f"❌ Нет данных для {symbol} ({timeframe})")
        return None
    
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# 🔹 Функция определения Order Blocks (OB)
def find_order_blocks(df):
    bullish_ob = df.iloc[-3]['low']
    bearish_ob = df.iloc[-3]['high']
    return bullish_ob, bearish_ob

# 🔹 Функция поиска Liquidity Zones
def find_liquidity_zones(df):
    support = df['low'].min()
    resistance = df['high'].max()
    return support, resistance

# 🔹 Функция поиска Fair Value Gap (FVG)
def find_fvg(df):
    fvg_up = None
    fvg_down = None
    for i in range(1, len(df) - 1):
        if df.iloc[i - 1]['high'] < df.iloc[i + 1]['low']:
            fvg_down = (df.iloc[i - 1]['high'], df.iloc[i + 1]['low'])
        if df.iloc[i - 1]['low'] > df.iloc[i + 1]['high']:
            fvg_up = (df.iloc[i - 1]['low'], df.iloc[i + 1]['high'])
    return fvg_up, fvg_down

# 🔹 Функция вычисления Break of Structure (BOS)
def find_bos(df):
    latest_high = df.iloc[-2]['high']
    latest_low = df.iloc[-2]['low']
    prev_high = df.iloc[-5]['high']
    prev_low = df.iloc[-5]['low']

    if latest_high > prev_high:
        return "BULLISH BOS"
    elif latest_low < prev_low:
        return "BEARISH BOS"
    return None

# 🔹 Функция вычисления Stochastic RSI
def stochastic_rsi(df, period=14):
    close_prices = df['close'].to_numpy()
    rsi = talib.RSI(close_prices, timeperiod=period)
    stoch_rsi = (rsi - np.min(rsi[-period:])) / (np.max(rsi[-period:]) - np.min(rsi[-period:])) * 100
    return stoch_rsi[-1]

# 🔹 Функция анализа рынка
def analyze_market(symbol):
    timeframes = ["1m", "5m", "15m"]
    signals = []

    for tf in timeframes:
        df = get_mt5_data(symbol, tf)
        if df is None:
            continue

        ob_low, ob_high = find_order_blocks(df)
        support, resistance = find_liquidity_zones(df)
        fvg_up, fvg_down = find_fvg(df)
        bos = find_bos(df)
        stoch_rsi_value = stochastic_rsi(df)

        print(f"🔎 {symbol} ({tf}) | OB: {ob_low}-{ob_high}, Liquidity: {support}-{resistance}, BOS: {bos}, FVG: {fvg_up}-{fvg_down}, Stoch RSI: {stoch_rsi_value:.2f}")

        # 🔹 Логика входа
        if bos == "BULLISH BOS" and stoch_rsi_value < 20 and ob_low:
            message = f"📈 Покупка XAU/USD ({tf})! Order Block: {ob_low}, TP: {resistance}, SL: {support}"
            signals.append(message)
        
        elif bos == "BEARISH BOS" and stoch_rsi_value > 80 and ob_high:
            message = f"📉 Продажа XAU/USD ({tf})! Order Block: {ob_high}, TP: {support}, SL: {resistance}"
            signals.append(message)

    return signals

# 🔹 Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# 🔹 Главный цикл бота
while True:
    print("📊 Анализируем рынок XAU/USD...")
    signals = analyze_market("XAUUSDm")

    if signals:
        for signal in signals:
            send_telegram_message(signal)

    time.sleep(60)  # Анализируем каждую минуту
