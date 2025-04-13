import streamlit as st
import yfinance as yf
import pandas as pd
import io

# --------------------- CONFIG ---------------------
st.set_page_config(page_title="AI Stock Monitor", layout="wide")
st.title("📈 AI-Powered Stock Portfolio Monitor")

# --------------------- USER INPUT ---------------------
with st.sidebar:
    st.header("Portfolio Settings")
    upload_file = st.file_uploader("Upload Portfolio CSV (Symbol, Quantity, Purchase Price):", type=["csv"])
    tickers_input = st.text_area("Or enter Stock Symbols (comma-separated):", value="AAPL, MSFT, NVDA")
    refresh = st.button("🔄 Refresh Data")

# --------------------- PORTFOLIO PROCESSING ---------------------
portfolio = None
if upload_file is not None:
    try:
        portfolio = pd.read_csv(upload_file)
        tickers = portfolio["Symbol"].astype(str).str.upper().tolist()
    except:
        st.error("Failed to read the uploaded file. Make sure it has 'Symbol', 'Quantity', 'Purchase Price' columns.")
else:
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]

# --------------------- DATA FETCHING ---------------------
def fetch_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="7d")
        info = stock.info
        return {
            "symbol": ticker,
            "price": info.get("regularMarketPrice"),
            "change": info.get("regularMarketChangePercent"),
            "sector": info.get("sector"),
            "name": info.get("shortName"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "rsi": calculate_rsi(hist["Close"])
        }
    except:
        return {"symbol": ticker, "error": "Data fetch failed"}

# --------------------- TECHNICAL INDICATORS ---------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2) if not rsi.empty else None

# --------------------- STRATEGY ENGINE ---------------------
def generate_signal(stock):
    if stock.get("error"):
        return "⚠️ Error"
    if stock["rsi"]:
        if stock["rsi"] < 30:
            return "🟢 Buy"
        elif stock["rsi"] > 70:
            return "🔴 Sell"
    return "🟡 Hold"

# --------------------- MAIN DISPLAY ---------------------
if tickers:
    data = [fetch_data(ticker) for ticker in tickers]
    for stock in data:
        stock["signal"] = generate_signal(stock)

    df = pd.DataFrame(data)

    if portfolio is not None:
        df = df.merge(portfolio, how="left", left_on="symbol", right_on="Symbol")
        df["Investment Value"] = df["price"] * df["Quantity"]
        df["Unrealized PnL"] = (df["price"] - df["Purchase Price"]) * df["Quantity"]
        df["PnL %"] = ((df["price"] - df["Purchase Price"]) / df["Purchase Price"]) * 100

        st.subheader("📦 Portfolio Overview")
        st.dataframe(df[["symbol", "name", "price", "Quantity", "Purchase Price", "Investment Value", "Unrealized PnL", "PnL %", "signal"]], use_container_width=True)
    else:
        st.subheader("📊 Stock Signals")
        st.dataframe(df[["symbol", "name", "price", "change", "rsi", "pe_ratio", "sector", "market_cap", "signal"]], use_container_width=True)
else:
    st.info("Enter at least one stock symbol or upload a portfolio CSV to get started.")
