"""
News source configuration for gold market sentiment analysis.
"""

NEWS_SOURCES = [
    {
        "name": "FXStreet News RSS",
        "url": "https://www.fxstreet.com/rss/news",
        "type": "rss",
        "filter_keywords": ["gold", "XAU", "bullion", "precious metal"],
    },
    {
        "name": "Google News Gold RSS",
        "url": "https://news.google.com/rss/search?q=gold+XAU+price&hl=en&gl=US&ceid=US:en",
        "type": "rss",
        "filter_keywords": None,
    },
    {
        "name": "Investing.com Economy RSS",
        "url": "https://www.investing.com/rss/news_14.rss",
        "type": "rss",
        "filter_keywords": ["gold", "XAU", "bullion", "Fed", "inflation", "dollar", "treasury", "Iran"],
    },
]
