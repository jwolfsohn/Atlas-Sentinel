"""
News Article Data Ingestion Pipeline
Simulates NewsAPI ingestion with sentiment analysis
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import random

from backend.data.data_simulator import DataSimulator


class NewsPipeline:
    """
    Ingests and stores news articles
    Simulates NewsAPI ingestion
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize pipeline
        
        Args:
            data_dir: Directory to store data files (defaults to .data/news)
        """
        if data_dir is None:
            data_dir = os.getenv('DATA_DIR', '.data')
        
        self.data_dir = Path(data_dir) / 'news'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.simulator = DataSimulator()
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
    
    def ingest_news_articles(self, 
                            port_id: Optional[str] = None,
                            region: Optional[str] = None,
                            limit: int = 10,
                            force_refresh: bool = False) -> List[Dict]:
        """
        Ingest news articles
        
        Args:
            port_id: Specific port to query
            region: Specific region to query
            limit: Maximum number of articles
            force_refresh: Force refresh even if cached
            
        Returns:
            List of news articles
        """
        cache_key = f"{port_id or region or 'all'}_{limit}"
        cache_file = self.data_dir / f"{cache_key}_articles.json"
        
        # Check cache
        if not force_refresh and cache_file.exists():
            cache_data = self._load_cache(cache_file)
            if cache_data and self._is_cache_valid(cache_data):
                return cache_data['data']
        
        # Generate articles
        articles = []
        article_count = random.randint(1, limit)
        
        if port_id:
            # Generate articles for specific port
            for _ in range(article_count):
                article = self.simulator.generate_news_article(port_id=port_id)
                articles.append(article)
        elif region:
            # Generate articles for region
            region_ports = [p for p in self.simulator.ports if p['region'] == region]
            for _ in range(article_count):
                port = random.choice(region_ports) if region_ports else None
                article = self.simulator.generate_news_article(
                    port_id=port['id'] if port else None,
                    region=region
                )
                articles.append(article)
        else:
            # Generate articles for all ports
            for _ in range(article_count):
                article = self.simulator.generate_news_article()
                articles.append(article)
        
        # Store in cache
        self._save_cache(cache_file, articles)
        
        # Store individual articles
        for article in articles:
            self._store_article(article)
        
        return articles
    
    def get_recent_articles(self, 
                           port_id: Optional[str] = None,
                           hours: int = 24,
                           min_sentiment: Optional[float] = None) -> List[Dict]:
        """
        Get recent articles with optional filtering
        
        Args:
            port_id: Filter by port
            hours: Time window in hours
            min_sentiment: Minimum sentiment score threshold (for negative sentiment)
            
        Returns:
            List of recent articles
        """
        articles_dir = self.data_dir / 'articles'
        if not articles_dir.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        articles = []
        
        for article_file in articles_dir.glob('*.json'):
            try:
                with open(article_file, 'r') as f:
                    article = json.load(f)
                
                article_time = datetime.fromisoformat(article['timestamp'])
                if article_time >= cutoff_time:
                    # Apply filters
                    if port_id and article.get('port_id') != port_id:
                        continue
                    
                    if min_sentiment is not None:
                        sentiment = article.get('sentiment_score', 0)
                        if sentiment > min_sentiment:  # More positive than threshold
                            continue
                    
                    articles.append(article)
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by timestamp (newest first)
        articles.sort(key=lambda a: a.get('timestamp', ''), reverse=True)
        
        return articles
    
    def get_articles_by_sentiment(self, 
                                 port_id: Optional[str] = None,
                                 negative_only: bool = True) -> Dict[str, List[Dict]]:
        """
        Group articles by sentiment
        
        Args:
            port_id: Filter by port
            negative_only: Only return negative sentiment articles
            
        Returns:
            Dict with 'negative' and 'positive' keys
        """
        articles = self.get_recent_articles(port_id=port_id, hours=168)  # Last week
        
        grouped = {'negative': [], 'positive': [], 'neutral': []}
        
        for article in articles:
            sentiment = article.get('sentiment_score', 0)
            if sentiment < -0.3:
                grouped['negative'].append(article)
            elif sentiment > 0.3:
                grouped['positive'].append(article)
            else:
                grouped['neutral'].append(article)
        
        if negative_only:
            return {'negative': grouped['negative']}
        
        return grouped
    
    def _store_article(self, article: Dict):
        """Store individual article"""
        article_id = article.get('article_id', f"article_{datetime.now().timestamp()}")
        article_file = self.data_dir / f"articles/{article_id}.json"
        article_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(article_file, 'w') as f:
            json.dump(article, f, indent=2)
    
    def _save_cache(self, cache_file: Path, data: List[Dict]):
        """Save data to cache file"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _load_cache(self, cache_file: Path) -> Optional[Dict]:
        """Load data from cache file"""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Check if cache is still valid"""
        if 'timestamp' not in cache_data:
            return False
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        return datetime.now() - cache_time < self.cache_duration

