import requests
import pandas as pd
import praw
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Download VADER lexicon (only needs to be done once)
nltk.download('vader_lexicon')

class TradingLogic:
    def __init__(self):
        self.simulated_balance = 10000  # Start with $10,000
        self.btc_position = 0  # No BTC initially
        self.last_trade = "No trade executed."
        self.price_data = []
        self.fear_greed_index = None
        self.fear_greed_classification = None
        self.commission_fee = 0.001  # 0.1% commission per trade

        # Reddit API Setup using environment variables
        self.reddit = praw.Reddit(
            client_id=os.environ.get('CLIENT_ID'),
            client_secret=os.environ.get('CLIENT_SECRET'),
            user_agent=os.environ.get('USER_AGENT', 'SentimentCollector')
        )

    # Method to fetch Fear and Greed Index from external API
    def fetch_fear_greed_index(self):
        try:
            url = 'https://api.alternative.me/fng/?limit=1'
            response = requests.get(url)
            data = response.json()
            if 'data' in data:
                self.fear_greed_index = int(data['data'][0]['value'])
                self.fear_greed_classification = data['data'][0]['value_classification']
        except Exception as e:
            print(f"Error fetching Fear and Greed Index: {e}")
            self.fear_greed_index, self.fear_greed_classification = None, None

    # Fetch Reddit sentiment
    def fetch_and_analyze_reddit(self, subreddit_name="Bitcoin", limit=30):
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = subreddit.hot(limit=limit)

        sia = SentimentIntensityAnalyzer()
        total_sentiment = 0
        post_count = 0

        for post in posts:
            title = post.title
            sentiment = sia.polarity_scores(title)
            total_sentiment += sentiment['compound']
            post_count += 1

        # Calculate average sentiment
        average_sentiment = total_sentiment / post_count if post_count > 0 else 0
        return average_sentiment

    # Update price data
    def update_price_data(self, price):
        self.price_data.append(price)
        if len(self.price_data) > 100:  # Keep only the last 100 prices
            self.price_data.pop(0)

    # Apply trading logic based on Fear & Greed Index, SMA, and Reddit Sentiment
    def apply_trading_logic(self):
        reason = "No trade executed."  # Default reason
        buy_score = 0  # Score for buying
        sell_score = 0  # Score for selling

        sma_score = 0
        fear_greed_score = 0
        sentiment_score = 0

        if len(self.price_data) >= 50:
            df = pd.DataFrame(self.price_data, columns=['close'])
            df['SMA20'] = df['close'].rolling(window=20).mean()
            df['SMA50'] = df['close'].rolling(window=50).mean()

            # Fetch Reddit sentiment
            reddit_sentiment = self.fetch_and_analyze_reddit("Bitcoin", limit=100)

            # Calculate SMA points
            sma_diff = df['SMA20'].iloc[-1] - df['SMA50'].iloc[-1]
            if sma_diff > 0:
                sma_score = sma_diff
                buy_score += sma_diff  # Positive difference adds to buy score
            else:
                sma_score = sma_diff
                sell_score += abs(sma_diff)  # Negative difference adds to sell score

            # Calculate Fear & Greed points
            if self.fear_greed_index is not None:
                fg_value = int(self.fear_greed_index)
                if fg_value <= 20:  # Extreme Fear, strong buy signal
                    fear_greed_score = 5
                    buy_score += 5
                elif fg_value <= 50:  # Fear or Neutral, moderate buy signal
                    fear_greed_score = 2
                    buy_score += 2
                elif fg_value >= 80:  # Extreme Greed, strong sell signal
                    fear_greed_score = 5
                    sell_score += 5
                elif fg_value >= 60:  # Greed, moderate sell signal
                    fear_greed_score = 2
                    sell_score += 2

            # Calculate Sentiment points
            if reddit_sentiment > 0.5:  # Strong positive sentiment
                sentiment_score = 3
                buy_score += 3
            elif reddit_sentiment > 0.2:  # Moderately positive sentiment
                sentiment_score = 1
                buy_score += 1
            elif reddit_sentiment < -0.5:  # Strong negative sentiment
                sentiment_score = 3
                sell_score += 3
            elif reddit_sentiment < -0.2:  # Moderately negative sentiment
                sentiment_score = 1
                sell_score += 1

            # **Threshold Logic**: Buy if buy_score ≥ 5, Sell if sell_score ≥ 5
            if buy_score >= 3.5 and self.btc_position == 0 and self.simulated_balance > 0:
                # Simulate buy
                self.btc_position = (self.simulated_balance * (1 - self.commission_fee)) / self.price_data[-1]
                self.simulated_balance = 0
                self.last_trade = f"Simulated Buy: {self.btc_position:.6f} BTC at ${self.price_data[-1]:.2f}"
                reason = f"Buy executed with a score of {buy_score}. Reason: Positive sentiment, favorable SMA, and Fear & Greed index."
                return "Buy", reason, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score
            elif sell_score >= 3.5 and self.btc_position > 0:
                # Simulate sell
                self.simulated_balance = self.btc_position * self.price_data[-1] * (1 - self.commission_fee)
                self.btc_position = 0
                self.last_trade = f"Simulated Sell: Converted to ${self.simulated_balance:.2f} USD at ${self.price_data[-1]:.2f}"
                reason = f"Sell executed with a score of {sell_score}. Reason: Negative sentiment, unfavorable SMA, and Fear & Greed index."
                return "Sell", reason, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score
            else:
                # No trade was made, explain why
                if self.btc_position == 0 and self.simulated_balance > 0:
                    reason = f"Hold: Insufficient buy score ({buy_score})"
                elif self.btc_position > 0:
                    reason = f"Hold: Insufficient sell score ({sell_score})"
                return "Hold", reason, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score

    # Get the state of the current balance, position, and last trade
    def get_state(self):
        return {
            'balance': self.simulated_balance,
            'btc_position': self.btc_position,
            'last_trade': self.last_trade,
            'fear_greed_index': self.fear_greed_index,
            'fear_greed_classification': self.fear_greed_classification
        }