import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# --- 1. Fetch price history from CoinGecko ---
def get_price_history(coin_id, days=90):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    data = requests.get(url, params=params).json()
    prices = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    prices["date"] = pd.to_datetime(prices["timestamp"], unit="ms").dt.date
    prices = prices.groupby("date")["price"].mean().reset_index()
    return prices


matic_hist = get_price_history("polygon", 90)
btc_hist = get_price_history("bitcoin", 90)
eth_hist = get_price_history("ethereum", 90)

# Merge and compute returns
df_prices = matic_hist.merge(btc_hist, on="date", suffixes=("_matic", "_btc"))
df_prices = df_prices.merge(eth_hist, on="date")
df_prices.rename(columns={"price": "price_eth"}, inplace=True)

for col in ["price_matic", "price_btc", "price_eth"]:
    df_prices[f"ret_{col.split('_')[-1]}"] = df_prices[col].pct_change()

# Correlations
corr_btc = df_prices["ret_matic"].corr(df_prices["ret_btc"])
corr_eth = df_prices["ret_matic"].corr(df_prices["ret_eth"])

# --- 2. Fetch on-chain metrics from DeFiLlama ---
# TVL
tvl_data = requests.get("https://api.llama.fi/tvl/polygon").json()
tvl = tvl_data[-1][1] if isinstance(tvl_data, list) else None

# Fees & active addresses
overview = requests.get("https://api.llama.fi/overview/polygon").json()
# This endpoint may vary — adapt if needed
fees_24h = overview.get("protocols", [{}])[0].get("fees24h", None)

# Dummy active addresses placeholder (replace with Polygonscan API if needed)
active_addresses = 625943  # placeholder


# --- 3. Scoring functions ---
def score_tvl(v):
    return 1.0 if v >= 2.5e9 else 0.7 if v >= 1.0e9 else 0.4 if v >= 5e8 else 0.2


def score_active_addr(v):
    return (
        1.0 if v >= 1_000_000 else 0.7 if v >= 500_000 else 0.4 if v >= 200_000 else 0.2
    )


def score_fees(v):
    return 1.0 if v >= 50_000 else 0.7 if v >= 10_000 else 0.4 if v >= 2_000 else 0.2


def score_fee_trend(v):
    return 1.0 if v >= 0.1 else 0.7 if v >= 0.0 else 0.4 if v >= -0.1 else 0.2


def score_corr(c):
    return 1.0 if c >= 0.8 else 0.6 if c >= 0.5 else 0.3


# --- 4. Apply scoring ---
scores = {
    "TVL_score": score_tvl(tvl),
    "ActiveAddr_score": score_active_addr(active_addresses),
    "Fees_score": score_fees(fees_24h or 0),
    "FeeTrend_score": score_fee_trend(-0.05),  # placeholder trend
    "BTCcorr_score": score_corr(corr_btc),
    "ETHcorr_score": score_corr(corr_eth),
    "Price_score": 0.5,
}

# New weights
weights = {
    "TVL_score": 0.20,
    "ActiveAddr_score": 0.20,
    "Fees_score": 0.10,
    "FeeTrend_score": 0.15,
    "BTCcorr_score": 0.15,
    "ETHcorr_score": 0.10,
    "Price_score": 0.10,
}

weighted_score = sum(scores[k] * weights[k] for k in scores)


def score_to_prob(score, horizon="end2025"):
    base = 0.05 + 0.85 * score
    return max(0.01, min(0.99, base * (0.45 if horizon == "end2025" else 0.85)))


prob_end2025 = score_to_prob(weighted_score, "end2025")
prob_2026 = score_to_prob(weighted_score, "2026")

# --- 5. Output ---
metrics_df = pd.DataFrame(
    [{"Metric": m, "Score": round(scores[m], 3), "Weight": weights[m]} for m in scores]
)

summary_df = pd.DataFrame(
    [
        {"Item": "Weighted Bullishness Score", "Value": round(weighted_score, 3)},
        {"Item": "Prob ≥50% gain by Dec 31, 2025", "Value": f"{prob_end2025:.2%}"},
        {"Item": "Prob ≥50% gain in 2026", "Value": f"{prob_2026:.2%}"},
    ]
)

metrics_df.to_csv("polygon_tracker_metrics.csv", index=False)
summary_df.to_csv("polygon_tracker_summary.csv", index=False)

print("Updated metrics:\n", metrics_df)
print("\nSummary:\n", summary_df)
