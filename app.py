import yfinance as yf
import pandas as pd
import json

# Voeg hier je gewenste US aandelen toe
tickers = ['AAPL', 'NVDA', 'TSLA', 'MDB', 'LXU', 'FIS', 'ALHC', 'MSFT', 'AMD']
results = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1y')
        if len(data) < 200:
            continue
            
        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']
        
        current_price = close.iloc[-1]
        sma20 = close.rolling(window=20).mean().iloc[-1]
        sma50 = close.rolling(window=50).mean().iloc[-1]
        sma200 = close.rolling(window=200).mean().iloc[-1]
        
        # RSI 14 berekening
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        # MACD (12, 26, 9) berekening
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        
        # Volume ratio t.o.v. 20-daags gemiddelde
        vol_sma20 = volume.rolling(window=20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        vol_ratio = current_vol / vol_sma20 if vol_sma20 > 0 else 1.0
        
        # Positie in 52-week range (%)
        high_52, low_52 = high.max(), low.min()
        range_pct = ((current_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) > 0 else 50.0
        
        # --- yrobot.us Scoring Logica (5 indicatoren) ---
        bullish_count = 0
        bearish_count = 0
        
        if current_price > sma50: bullish_count += 1
        else: bearish_count += 1
        
        if current_price > sma200: bullish_count += 1
        else: bearish_count += 1
        
        if sma50 > sma200: bullish_count += 1  # Golden cross
        else: bearish_count += 1                # Death cross
        
        if rsi_val > 50: bullish_count += 1     # Momentum boven middenlijn
        else: bearish_count += 1
        
        if macd_val > signal_val: bullish_count += 1
        else: bearish_count += 1
        
        # Rating bepalen op basis van score
        if bullish_count >= 4: rating = "Bullish"
        elif bullish_count == 3: rating = "Leaning Bullish"
        elif bullish_count == 2: rating = "Hold / Neutraal"
        elif bullish_count == 1: rating = "Leaning Bearish"
        else: rating = "Bearish"
        
        results.append({
            "ticker": ticker,
            "price": round(current_price, 2),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "rsi": round(rsi_val, 2),
            "macd": round(macd_val, 2),
            "signal": round(signal_val, 2),
            "vol_ratio": round(vol_ratio, 2),
            "range_pct": round(range_pct, 1),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "rating": rating
        })
    except Exception as e:
        print(f"Fout bij {ticker}: {e}")

# Sorteer op sterkste bullische score eerst
results.sort(key=lambda x: x['bullish_count'], reverse=True)

# Opslaan als JSON voor het frontend dashboard
with open('scan_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"Scan voltooid! {len(results)} aandelen verwerkt en opgeslagen in scan_results.json")
