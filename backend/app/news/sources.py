"""
News source configuration for market sentiment analysis (per-symbol).
"""

# ─── Shared: Trump / Trade Policy / Geopolitics (affects ALL markets) ─────────
_TRUMP_TRADE_SOURCES = [
    {"name": "Google News Trump Tariff", "url": "https://news.google.com/rss/search?q=Trump+tariff+trade+war&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
    {"name": "Google News US Trade Policy", "url": "https://news.google.com/rss/search?q=US+trade+policy+sanctions+tariff&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
]

NEWS_SOURCES_BY_SYMBOL = {
    "GOLD": [
        {"name": "FXStreet News RSS", "url": "https://www.fxstreet.com/rss/news", "type": "rss", "filter_keywords": ["gold", "XAU", "bullion", "precious metal"]},
        {"name": "Google News Gold RSS", "url": "https://news.google.com/rss/search?q=gold+XAU+price&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
        {"name": "Investing.com Economy RSS", "url": "https://www.investing.com/rss/news_14.rss", "type": "rss", "filter_keywords": ["gold", "XAU", "bullion", "Fed", "inflation", "dollar", "treasury"]},
        *_TRUMP_TRADE_SOURCES,
    ],
    "OILCash": [
        {"name": "Google News Oil RSS", "url": "https://news.google.com/rss/search?q=crude+oil+WTI+price&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
        {"name": "Investing.com Economy RSS", "url": "https://www.investing.com/rss/news_14.rss", "type": "rss", "filter_keywords": ["oil", "crude", "WTI", "OPEC", "energy", "petroleum"]},
        *_TRUMP_TRADE_SOURCES,
    ],
    "BTCUSD": [
        {"name": "Google News Bitcoin RSS", "url": "https://news.google.com/rss/search?q=bitcoin+BTC+crypto+price&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
        {"name": "Investing.com Economy RSS", "url": "https://www.investing.com/rss/news_14.rss", "type": "rss", "filter_keywords": ["bitcoin", "crypto", "BTC", "blockchain", "SEC"]},
        *_TRUMP_TRADE_SOURCES,
    ],
    "USDJPY": [
        {"name": "Google News USDJPY RSS", "url": "https://news.google.com/rss/search?q=USDJPY+yen+dollar+BOJ&hl=en&gl=US&ceid=US:en", "type": "rss", "filter_keywords": None},
        {"name": "Investing.com Economy RSS", "url": "https://www.investing.com/rss/news_14.rss", "type": "rss", "filter_keywords": ["yen", "JPY", "BOJ", "Japan", "dollar", "Fed"]},
        *_TRUMP_TRADE_SOURCES,
    ],
}

# Keep backward compat
NEWS_SOURCES = NEWS_SOURCES_BY_SYMBOL.get("GOLD", [])
