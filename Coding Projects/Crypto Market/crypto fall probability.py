import numpy as np

import pandas as pd
from datetime import datetime


class MarketProbabilityAnalyzer:
    """
    Analyzes the probability of a cryptocurrency market fall using economic factors.
    """
    def __init__(self):

        self.economic_factors = {
            "interest_rate": 0.0425,  # 4.25%
            "inflation_rate": 0.031,  # 3.1%
            "gdp_growth": 0.022,  # 2.2%
            "unemployment_rate": 0.036,  # 3.6%
        }


        self.social_factors = {
            "market_sentiment": 0.3,
            "social_media_buzz": 0.4,
            "news_sentiment": 0.25,
        }


        self.volatility = {
            "stocks": 0.18,  # 18% annual volatility
            "crypto": 0.65,  # 65% annual volatility
        }

    def calculate_base_probability(self, asset_type="stocks"):


        econ_score = (
            self.economic_factors["gdp_growth"]
            - self.economic_factors["interest_rate"]
            - self.economic_factors["inflation_rate"]
            + (0.1 - self.economic_factors["unemployment_rate"])
        ) / 4


        social_score = (
            self.social_factors["market_sentiment"]
            + self.social_factors["social_media_buzz"]
            + self.social_factors["news_sentiment"]
        ) / 3


        volatility = self.volatility[asset_type]
        base_prob = (econ_score + social_score) * volatility + 0.5


        return max(0.1, min(0.9, base_prob))

    def simulate_price_movement(self, current_price, days=30, asset_type="stocks"):

        n_simulations = 10000
        volatility = self.volatility[asset_type]
        base_prob = self.calculate_base_probability(asset_type)


        daily_returns = np.random.normal(


            loc=base_prob / 252,
            scale=volatility / np.sqrt(252),
            size=(days, n_simulations),
        )


        price_paths = current_price * np.exp(np.cumsum(daily_returns, axis=0))

        return price_paths

    def calculate_drop_probability(
        self, current_price, threshold_percent, days=30, asset_type="stocks"
    ):

        price_paths = self.simulate_price_movement(current_price, days, asset_type)


        final_prices = price_paths[-1]


        drop_threshold = current_price * (1 - threshold_percent / 100)
        drops = final_prices < drop_threshold


        drop_prob = np.mean(drops)

        return drop_prob, final_prices

    def analyze_market(self, stock_price=100, crypto_price=50000):



        thresholds = [5, 10, 20, 30]
        results = {"stocks": {}, "crypto": {}}

        for threshold in thresholds:

            stock_prob, stock_prices = self.calculate_drop_probability(
                stock_price, threshold, asset_type="stocks"
            )
            results["stocks"][f"{threshold}%"] = {
                "drop_probability": stock_prob,
                "expected_price": np.mean(stock_prices),
            }


            crypto_prob, crypto_prices = self.calculate_drop_probability(
                crypto_price, threshold, asset_type="crypto"
            )
            results["crypto"][f"{threshold}%"] = {
                "drop_probability": crypto_prob,
                "expected_price": np.mean(crypto_prices),
            }

        return results



def main():
    analyzer = MarketProbabilityAnalyzer()


    results = analyzer.analyze_market(


        stock_price=100,
        crypto_price=50000,
    )


    print(f"Market Analysis - Date: {datetime.now().strftime('%Y-%m-%d')}")
    print("\nStock Market Probabilities:")
    for threshold, data in results["stocks"].items():
        print(f"Probability of {threshold} drop: {data['drop_probability']:.2%}")
        print(f"Expected price after 30 days: ${data['expected_price']:.2f}")

    print("\nCrypto Market Probabilities:")
    for threshold, data in results["crypto"].items():
        print(f"Probability of {threshold} drop: {data['drop_probability']:.2%}")
        print(f"Expected price after 30 days: ${data['expected_price']:.2f}")


if __name__ == "__main__":
    main()
