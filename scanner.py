import yfinance as yf
import pandas as pd
import json
import warnings

warnings.filterwarnings('ignore')

# Voeg hier je gewenste aandelen toe
tickers = ['AAPL', 'NVDA', 'TSLA', 'MDB', 'LXU', 'FIS', 'ALHC', 'MSFT', 'AMD', 'PLTR', 'SMCI']
results = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # 2 jaar historie voor betrouwbare SMA200 en 52-weeks data
        hist = stock.history(period='2y')
        
        if len(hist) < 200:
            continue
            
        close = hist['Close']
        current_price = close.iloc[-1]
        
        # 1. Fair Value ophalen uit gratis yfinance info (Analyst Target Price)
        info = stock.info
        target_price = info.get('targetMeanPrice', None)
        fair_value_gap_pct = ((target_price - current_price) / current_price * 100) if target_price else None
        
        # 2. Technische Indicatoren berekenen
        sma20 = close.rolling(window=20).mean().iloc[-1]
        sma50 = close.rolling(window=50).mean().iloc[-1]
        sma200 = close.rolling(window=200).mean().iloc[-1]
        
        # RSI 14
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        # MACD (12, 26, 9)
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        
        # Volume ratio t.o.v. 20-daags gemiddelde
        volume = hist['Volume']
        vol_sma20 = volume.rolling(window=20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        vol_ratio = current_vol / vol_sma20 if vol_sma20 > 0 else 1.0
        
        # 52-week range (op basis van de laatste ~252 handelsdagen)
        high_52 = hist['High'].tail(252).max()
        low_52 = hist['Low'].tail(252).min()
        range_pct = ((current_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) > 0 else 50.0
        
        # 3. yrobot.us Scoring Logica (5 indicatoren)
        bullish_count = 0
        indicators = {}
        
        if current_price > sma50:
            bullish_count += 1
            indicators['sma50'] = 'Bullish'
        else:
            indicators['sma50'] = 'Bearish'
            
        if current_price > sma200:
            bullish_count += 1
            indicators['sma200'] = 'Bullish'
        else:
            indicators['sma200'] = 'Bearish'
            
        if sma50 > sma200:
            bullish_count += 1
            indicators['trend'] = 'Golden Cross'
        else:
            indicators['trend'] = 'Death Cross'
            
        if rsi_val > 50:
            bullish_count += 1
            indicators['rsi'] = 'Bullish'
        else:
            indicators['rsi'] = 'Bearish'
            
        if macd_val > signal_val:
            bullish_count += 1
            indicators['macd'] = 'Bullish'
        else:
            indicators['macd'] = 'Bearish'
            
        # Rating bepalen
        if bullish_count >= 4: rating = "Strong Buy"
        elif bullish_count == 3: rating = "Buy"
        elif bullish_count == 2: rating = "Hold"
        elif bullish_count == 1: rating = "Sell"
        else: rating = "Strong Sell"
        
        results.append({
            "ticker": ticker,
            "price": round(current_price, 2),
            "target_price": round(target_price, 2) if target_price else None,
            "fair_value_gap_pct": round(fair_value_gap_pct, 1) if fair_value_gap_pct else None,
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "rsi": round(rsi_val, 2),
            "macd": round(macd_val, 3),
            "signal": round(signal_val, 3),
            "vol_ratio": round(vol_ratio, 2),
            "high_52": round(high_52, 2),
            "low_52": round(low_52, 2),
            "range_pct": round(range_pct, 1),
            "bullish_count": bullish_count,
            "indicators": indicators,
            "rating": rating
        })
    except Exception as e:
        print(f"Fout bij {ticker}: {e}")

# Sorteer op sterkste score eerst
results.sort(key=lambda x: x['bullish_count'], reverse=True)

# Opslaan als JSON voor het frontend dashboard
with open('scan_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"✅ Scan voltooid! {len(results)} aandelen verwerkt en opgeslagen in scan_results.json")
