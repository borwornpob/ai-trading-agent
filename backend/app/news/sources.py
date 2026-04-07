"""
News source configuration for gold market sentiment analysis.
"""

NEWS_SOURCES = [
    {
        "name": "Kitco News RSS",
        "url": "https://www.kitco.com/rss/news.xml",
        "type": "rss",
        "filter_keywords": None,
    },
    {
        "name": "Reuters Business RSS",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "rss",
        "filter_keywords": ["gold", "XAU", "bullion", "Fed", "inflation", "dollar", "treasury"],
    },
]
