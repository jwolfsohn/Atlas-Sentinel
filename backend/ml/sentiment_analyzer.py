"""
Sentiment Analysis for News Articles
Uses transformer models for real-time sentiment scoring
"""

from typing import List, Dict, Optional
import numpy as np
from datetime import datetime


class SentimentAnalyzer:
    """
    Analyzes news article sentiment using transformer models
    Can use OpenAI API or local HuggingFace models
    """
    
    def __init__(self, use_openai: bool = False, api_key: Optional[str] = None):
        """
        Initialize sentiment analyzer
        
        Args:
            use_openai: Whether to use OpenAI API (requires API key)
            api_key: OpenAI API key if using OpenAI
        """
        self.use_openai = use_openai
        self.api_key = api_key
        
        # Urgency keywords that indicate supply chain disruption
        self.urgency_keywords = [
            'delay', 'disruption', 'closure', 'shutdown', 'strike',
            'congestion', 'backlog', 'shortage', 'crisis', 'emergency',
            'blockade', 'storm', 'hurricane', 'typhoon', 'flood',
            'accident', 'incident', 'breakdown', 'failure', 'outage'
        ]
        
        # Initialize model (in production, would load actual model)
        self.model_loaded = False
    
    def _load_model(self):
        """Load sentiment analysis model"""
        if self.use_openai:
            # Would initialize OpenAI client here
            pass
        else:
            # Would load HuggingFace model here
            # from transformers import pipeline
            # self.sentiment_pipeline = pipeline("sentiment-analysis", 
            #                                    model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            pass
        self.model_loaded = True
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment_score (-1 to 1) and label
        """
        if not self.model_loaded:
            self._load_model()
        
        # Simulated sentiment analysis (replace with actual model in production)
        # In production, this would call the actual model
        text_lower = text.lower()
        
        # Simple keyword-based scoring (would use ML model in production)
        negative_words = ['delay', 'disruption', 'problem', 'issue', 'crisis', 'failure']
        positive_words = ['smooth', 'efficient', 'resolved', 'improved', 'success']
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        # Score: -1 (very negative) to 1 (very positive)
        if negative_count > positive_count:
            sentiment_score = -0.5 - (negative_count * 0.1)
        elif positive_count > negative_count:
            sentiment_score = 0.3 + (positive_count * 0.1)
        else:
            sentiment_score = 0.0
        
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine label
        if sentiment_score < -0.3:
            label = 'negative'
        elif sentiment_score > 0.3:
            label = 'positive'
        else:
            label = 'neutral'
        
        return {
            'sentiment_score': sentiment_score,
            'label': label,
            'confidence': 0.75  # Would come from model in production
        }
    
    def analyze_articles(self, articles: List[Dict]) -> Dict:
        """
        Analyze multiple news articles and aggregate results
        
        Args:
            articles: List of article dicts with 'title', 'content', 'source', etc.
            
        Returns:
            Aggregated sentiment analysis
        """
        if not articles:
            return {
                'sentiment_score': 0.0,
                'article_count': 0,
                'urgency_keywords': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Analyze each article
        sentiment_scores = []
        total_urgency_keywords = 0
        
        for article in articles:
            # Combine title and content
            text = f"{article.get('title', '')} {article.get('content', '')}"
            
            # Analyze sentiment
            analysis = self.analyze_text(text)
            sentiment_scores.append(analysis['sentiment_score'])
            
            # Count urgency keywords
            text_lower = text.lower()
            urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text_lower)
            total_urgency_keywords += urgency_count
        
        # Aggregate scores
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            'sentiment_score': float(avg_sentiment),
            'article_count': len(articles),
            'urgency_keywords': total_urgency_keywords,
            'individual_scores': sentiment_scores,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_region(self, region_name: str, articles: List[Dict]) -> Dict:
        """
        Analyze sentiment for a specific region
        
        Args:
            region_name: Name of the region/port
            articles: Articles related to that region
            
        Returns:
            Region-specific sentiment analysis
        """
        analysis = self.analyze_articles(articles)
        analysis['region'] = region_name
        return analysis

