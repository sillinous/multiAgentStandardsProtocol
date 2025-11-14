"""
Text Sentiment Analyzer

Performs NLP-based sentiment analysis on text content
using various techniques including keyword matching,
pattern recognition, and simple ML approaches.

Note: In production, integrate with services like:
- TextBlob
- VADER Sentiment
- OpenAI API
- Custom fine-tuned models
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
import re
from collections import Counter


# ============================================================================
# Sentiment Lexicons
# ============================================================================

# Positive financial keywords
POSITIVE_KEYWORDS = {
    'bullish', 'growth', 'profit', 'gain', 'rally', 'surge', 'soar',
    'breakout', 'upgrade', 'beat', 'exceed', 'outperform', 'strong',
    'momentum', 'recovery', 'expansion', 'innovation', 'breakthrough',
    'record', 'high', 'success', 'positive', 'optimistic', 'confident',
    'buy', 'long', 'calls', 'moon', 'rocket', '🚀', '📈', '💎',
    'winner', 'gem', 'opportunity', 'potential', 'promising'
}

# Negative financial keywords
NEGATIVE_KEYWORDS = {
    'bearish', 'loss', 'decline', 'fall', 'drop', 'crash', 'plunge',
    'breakdown', 'downgrade', 'miss', 'underperform', 'weak', 'concern',
    'recession', 'contraction', 'risk', 'warning', 'low', 'fail',
    'negative', 'pessimistic', 'worried', 'sell', 'short', 'puts',
    'dump', 'bag', 'loser', 'overvalued', 'bubble', 'red', '📉', '💀',
    'bankruptcy', 'layoff', 'trouble', 'crisis'
}

# Intensity modifiers
INTENSIFIERS = {
    'very', 'extremely', 'highly', 'significantly', 'substantially',
    'dramatically', 'massively', 'huge', 'tremendous', 'incredible'
}

DIMINISHERS = {
    'slightly', 'somewhat', 'moderately', 'fairly', 'relatively',
    'barely', 'hardly', 'marginally', 'little'
}

# Negation words
NEGATIONS = {
    'not', 'no', 'never', 'none', 'nothing', 'nobody', 'neither',
    'nowhere', 'cant', "can't", 'dont', "don't", 'wont', "won't",
    'shouldnt', "shouldn't", 'isnt', "isn't", 'arent', "aren't"
}


# ============================================================================
# Text Sentiment Analyzer
# ============================================================================

class TextSentimentAnalyzer:
    """
    Analyzes sentiment of text content

    Uses keyword matching, pattern recognition, and context analysis
    to determine sentiment polarity and intensity.

    Example:
        analyzer = TextSentimentAnalyzer()

        text = "Apple reports strong earnings, stock surges 10%"
        score, confidence = analyzer.analyze(text)

        print(f"Sentiment: {score:.2f}")  # 0.75 (positive)
        print(f"Confidence: {confidence:.2f}")  # 0.85
    """

    def __init__(
        self,
        positive_keywords: Optional[Set[str]] = None,
        negative_keywords: Optional[Set[str]] = None
    ):
        """
        Initialize analyzer with keyword lexicons

        Args:
            positive_keywords: Custom positive keywords (optional)
            negative_keywords: Custom negative keywords (optional)
        """
        self.positive_keywords = positive_keywords or POSITIVE_KEYWORDS
        self.negative_keywords = negative_keywords or NEGATIVE_KEYWORDS

    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            (score, confidence) where score is -1.0 to +1.0
        """
        if not text or not text.strip():
            return 0.0, 0.0

        # Preprocess
        text = text.lower()
        words = self._tokenize(text)

        if not words:
            return 0.0, 0.0

        # Count positive and negative words
        pos_count = 0
        neg_count = 0
        total_keywords = 0

        for i, word in enumerate(words):
            # Check if negated
            is_negated = self._is_negated(words, i)

            # Check if word is sentiment keyword
            if word in self.positive_keywords:
                # Check for intensifiers/diminishers
                intensity = self._get_intensity(words, i)

                if is_negated:
                    neg_count += intensity
                else:
                    pos_count += intensity
                total_keywords += 1

            elif word in self.negative_keywords:
                intensity = self._get_intensity(words, i)

                if is_negated:
                    pos_count += intensity
                else:
                    neg_count += intensity
                total_keywords += 1

        # Calculate score
        if total_keywords == 0:
            return 0.0, 0.0

        # Normalize by total words (reduce impact of length)
        pos_ratio = pos_count / len(words)
        neg_ratio = neg_count / len(words)

        # Score from -1 to +1
        score = (pos_ratio - neg_ratio) * 10  # Scale up
        score = max(min(score, 1.0), -1.0)  # Clamp

        # Confidence based on keyword density
        keyword_density = total_keywords / len(words)
        confidence = min(keyword_density * 5, 1.0)  # Scale and clamp

        return score, confidence

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove special characters except emojis
        text = re.sub(r'[^\w\s🚀📈📉💎💀]', ' ', text)

        # Split and filter
        words = text.split()
        words = [w.strip() for w in words if w.strip()]

        return words

    def _is_negated(self, words: List[str], index: int) -> bool:
        """Check if word at index is negated"""
        # Look back up to 3 words
        for i in range(max(0, index - 3), index):
            if words[i] in NEGATIONS:
                return True
        return False

    def _get_intensity(self, words: List[str], index: int) -> float:
        """Get intensity modifier for word at index"""
        # Look back 1-2 words for modifiers
        for i in range(max(0, index - 2), index):
            if words[i] in INTENSIFIERS:
                return 1.5
            elif words[i] in DIMINISHERS:
                return 0.5

        return 1.0

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract most important keywords from text"""
        words = self._tokenize(text.lower())

        # Filter to sentiment keywords only
        sentiment_words = [
            w for w in words
            if w in self.positive_keywords or w in self.negative_keywords
        ]

        # Count frequency
        counts = Counter(sentiment_words)

        # Return top N
        return [word for word, _ in counts.most_common(top_n)]


# ============================================================================
# Keyword Extractor
# ============================================================================

class KeywordExtractor:
    """
    Extracts important keywords and topics from text

    Uses frequency analysis and TF-IDF-like scoring
    to identify key terms.
    """

    # Common stop words to filter out
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their',
        'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }

    @staticmethod
    def extract(text: str, top_n: int = 10) -> List[str]:
        """
        Extract top N keywords from text

        Args:
            text: Text to analyze
            top_n: Number of keywords to return

        Returns:
            List of keywords
        """
        if not text:
            return []

        # Tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)

        # Filter stop words and short words
        words = [
            w for w in words
            if w not in KeywordExtractor.STOP_WORDS and len(w) > 3
        ]

        # Count frequency
        counts = Counter(words)

        # Return top N
        return [word for word, _ in counts.most_common(top_n)]

    @staticmethod
    def extract_phrases(text: str, top_n: int = 5) -> List[str]:
        """
        Extract common phrases (bigrams and trigrams)

        Args:
            text: Text to analyze
            top_n: Number of phrases to return

        Returns:
            List of phrases
        """
        if not text:
            return []

        # Tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)

        # Generate bigrams
        bigrams = [
            f"{words[i]} {words[i+1]}"
            for i in range(len(words) - 1)
        ]

        # Generate trigrams
        trigrams = [
            f"{words[i]} {words[i+1]} {words[i+2]}"
            for i in range(len(words) - 2)
        ]

        # Combine and count
        phrases = bigrams + trigrams
        counts = Counter(phrases)

        # Return top N
        return [phrase for phrase, _ in counts.most_common(top_n)]


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_sentiment_change(
    previous_score: float,
    current_score: float
) -> Tuple[float, str]:
    """
    Calculate change in sentiment

    Returns:
        (change, direction) where direction is "improving", "declining", "stable"
    """
    change = current_score - previous_score

    if change > 0.1:
        return change, "improving"
    elif change < -0.1:
        return change, "declining"
    else:
        return change, "stable"
