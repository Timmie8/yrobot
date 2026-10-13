import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Pagina configuratie
st.set_page_config(
    page_title="Aandelen Scanner Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS voor donker thema en kleurcodering
st.markdown("""
<style>
    .main {
        background-color: #0b1120;
    }
    .stApp {
        background-color: #0b1120;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #334155;
    }
    .indicator-card {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #334155;
        text-align: center;
    }
    .bullish {
        color: #22c55e !important;
        font-weight: bold;
    }
    .bearish {
        color: #ef4444 !important;
        font-weight: bold;
    }
    .neutral {
        color: #f59e0b !important;
        font-weight: bold;
    }
    .badge-bullish {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-bearish {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-neutral {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Titel
st.markdown("# 📈 Markt Scanner Dashboard")
st.markdown("**Gratis Yahoo Finance data • SMA, RSI, MACD & Fair Value analyse**")
st.markdown("---")

# Sidebar voor ticker selectie
st.sidebar.header("⚙️ Instellingen")
default_tickers = "AAPL,NVDA,TSLA,MDB,LXU,FIS,ALHC,MSFT,AMD,PLTR,SMCI"
ticker_input = st.sidebar.text_area(
    "Voer tickers in (gescheiden door komma's):",
    value=default_tickers,
    height=100
)

# Parse tickers
tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

# Scan knop
scan_button = st.sidebar.button("🔍 Start Scan", type="primary", use_container_width=True)

# Functie om technische indicatoren te berekenen
def calculate_indicators(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='2y')
        
        if len(hist) < 200:
            return None
            
        close = hist['Close']
        current_price = close.iloc[-1]
        
        # Fair Value (Analyst Target Price)
        info = stock.info
        target_price = info.get('targetMeanPrice', None)
        fair_value_gap_pct = ((target_price - current_price) / current_price * 100) if target_price else None
        
        # Technische Indicatoren
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
        
        # Volume ratio
        volume = hist['Volume']
        vol_sma20 = volume.rolling(window=20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        vol_ratio = current_vol / vol_sma20 if vol_sma20 > 0 else 1.0
        
        # 52-week range
        high_52 = hist['High'].tail(252).max()
        low_52 = hist['Low'].tail(252).min()
        range_pct = ((current_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) > 0 else 50.0
        
        # Scoring
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
            
        # Rating
        if bullish_count >= 4:
            rating = "Strong Buy"
        elif bullish_count == 3:
            rating = "Buy"
        elif bullish_count == 2:
            rating = "Hold"
        elif bullish_count == 1:
            rating = "Sell"
        else:
            rating = "Strong Sell"
        
        return {
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
        }
    except Exception as e:
        st.error(f"Fout bij {ticker}: {e}")
        return None

# Functie om chart te maken
def create_chart(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1y')
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} Prijs', 'Volume')
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Prijs'
        ),
        row=1, col=1
    )
    
    # SMA 50
    sma50 = hist['Close'].rolling(window=50).mean()
    fig.add_trace(
        go.Scatter(x=hist.index, y=sma50, name='SMA 50', line=dict(color='orange', width=1)),
        row=1, col=1
    )
    
    # SMA 200
    sma200 = hist['Close'].rolling(window=200).mean()
    fig.add_trace(
        go.Scatter(x=hist.index, y=sma200, name='SMA 200', line=dict(color='purple', width=1)),
        row=1, col=1
    )
    
    # Volume
    colors = ['green' if row['Close'] >= row['Open'] else 'red' for index, row in hist.iterrows()]
    fig.add_trace(
        go.Bar(x=hist.index, y=hist['Volume'], name='Volume', marker_color=colors),
        row=2, col=1
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

# Helper functie voor indicator badge
def get_indicator_badge(status):
    if status in ['Bullish', 'Golden Cross']:
        return f'<span class="badge-bullish">{status}</span>'
    elif status in ['Bearish', 'Death Cross']:
        return f'<span class="badge-bearish">{status}</span>'
    else:
        return f'<span class="badge-neutral">{status}</span>'

# Main app logic
if scan_button or 'scan_results' in st.session_state:
    if scan_button:
        with st.spinner(f"Scannen van {len(tickers)} aandelen..."):
            results = []
            progress_bar = st.progress(0)
            
            for idx, ticker in enumerate(tickers):
                result = calculate_indicators(ticker)
                if result:
                    results.append(result)
                progress_bar.progress((idx + 1) / len(tickers))
            
            # Sorteer op sterkste score
            results.sort(key=lambda x: x['bullish_count'], reverse=True)
            st.session_state.scan_results = results
    
    results = st.session_state.scan_results
    
    if results:
        # Resultaten tabel
        st.markdown("### 📊 Scan Resultaten")
        
        # Maak DataFrame voor display
        df_display = pd.DataFrame([
            {
                'Ticker': r['ticker'],
                'Prijs': f"${r['price']}",
                'Rating': r['rating'],
                'RSI': r['rsi'],
                'Fair Value Gap': f"{r['fair_value_gap_pct']:+.1f}%" if r['fair_value_gap_pct'] else 'N/A',
                'Score': f"{r['bullish_count']}/5"
            }
            for r in results
        ])
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Selecteer aandeel voor detail view
        selected_ticker = st.selectbox(
            "Selecteer een aandeel voor gedetailleerde analyse:",
            options=[r['ticker'] for r in results]
        )
        
        selected_data = next(r for r in results if r['ticker'] == selected_ticker)
        
        # Detail view
        st.markdown(f"### 📈 {selected_ticker} Analyse")
        
        # Rating badge met kleur
        if "Buy" in selected_data['rating']:
            rating_html = f'<span class="badge-bullish" style="font-size: 1rem; padding: 0.5rem 1rem;">{selected_data["rating"]} ({selected_data["bullish_count"]}/5 bullish)</span>'
        elif "Sell" in selected_data['rating']:
            rating_html = f'<span class="badge-bearish" style="font-size: 1rem; padding: 0.5rem 1rem;">{selected_data["rating"]} ({selected_data["bullish_count"]}/5 bullish)</span>'
        else:
            rating_html = f'<span class="badge-neutral" style="font-size: 1rem; padding: 0.5rem 1rem;">{selected_data["rating"]} ({selected_data["bullish_count"]}/5 bullish)</span>'
        
        st.markdown(rating_html, unsafe_allow_html=True)
        
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Huidige Prijs", f"${selected_data['price']}")
        
        with col2:
            fvg_text = f"{selected_data['fair_value_gap_pct']:+.1f}%" if selected_data['fair_value_gap_pct'] else "N/A"
            st.metric("Fair Value Gap", fvg_text)
        
        with col3:
            target_text = f"${selected_data['target_price']}" if selected_data['target_price'] else "N/A"
            st.metric("Doelkoers", target_text)
        
        with col4:
            st.metric("52-Week Range", f"{selected_data['range_pct']:.0f}%", 
                     help=f"${selected_data['low_52']} - ${selected_data['high_52']}")
        
        st.markdown("---")
        
        # Indicator details met custom kleuren
        st.markdown("#### 🔍 Technische Indicatoren")
        
        ind_col1, ind_col2, ind_col3, ind_col4, ind_col5 = st.columns(5)
        
        with ind_col1:
            sma50_status = selected_data['indicators']['sma50']
            badge = get_indicator_badge(sma50_status)
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">SMA 50</div>
                <div style="color: white; font-size: 1.25rem; font-weight: bold; margin-bottom: 0.5rem;">${selected_data['sma50']}</div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with ind_col2:
            sma200_status = selected_data['indicators']['sma200']
            badge = get_indicator_badge(sma200_status)
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">SMA 200</div>
                <div style="color: white; font-size: 1.25rem; font-weight: bold; margin-bottom: 0.5rem;">${selected_data['sma200']}</div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with ind_col3:
            rsi_status = selected_data['indicators']['rsi']
            badge = get_indicator_badge(rsi_status)
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">RSI (14)</div>
                <div style="color: white; font-size: 1.25rem; font-weight: bold; margin-bottom: 0.5rem;">{selected_data['rsi']}</div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with ind_col4:
            macd_status = selected_data['indicators']['macd']
            badge = get_indicator_badge(macd_status)
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">MACD</div>
                <div style="color: white; font-size: 1.25rem; font-weight: bold; margin-bottom: 0.5rem;">{selected_data['macd']}</div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with ind_col5:
            trend_status = selected_data['indicators']['trend']
            badge = get_indicator_badge(trend_status)
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">Trend</div>
                <div style="color: white; font-size: 1rem; font-weight: bold; margin-bottom: 0.5rem;">Vol: {selected_data['vol_ratio']}x</div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Chart
        st.markdown("#### 📊 Prijsgrafiek (1 jaar)")
        fig = create_chart(selected_ticker)
        st.plotly_chart(fig, use_container_width=True)
        
        # Timestamp
        st.markdown(f"*Laatste update: {datetime.now().strftime('%d-%m-%Y %H:%M')}*")

else:
    st.info("👈 Klik op 'Start Scan' in de sidebar om te beginnen")
