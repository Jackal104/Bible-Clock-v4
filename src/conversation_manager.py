#!/usr/bin/env python3
"""
Conversation Manager for Bible Clock v3
Handles multi-turn conversations, metrics, and session management.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import uuid
import re

logger = logging.getLogger(__name__)

@dataclass
class LightweightMetrics:
    """Lightweight metrics for long-term storage (no full text)."""
    date: str  # YYYY-MM-DD format
    category: str
    keywords: List[str]  # Top keywords extracted
    response_time: float
    success: bool
    hour: int  # 0-23 for hourly trends

@dataclass  
class AggregatedMetrics:
    """Daily aggregated metrics to save space."""
    date: str
    total_conversations: int
    categories: Dict[str, int]  # category -> count
    keywords: Dict[str, int]   # keyword -> count  
    avg_response_time: float
    success_rate: float
    hourly_distribution: Dict[int, int]  # hour -> count
    
@dataclass
class ConversationMetrics:
    """Full metrics for recent conversations (purged after 7 days)."""
    session_id: str
    timestamp: str
    question: str
    question_category: str
    speech_recognition_time: float
    chatgpt_processing_time: float
    tts_generation_time: float
    total_response_time: float
    response_length: int
    success: bool
    error_message: Optional[str] = None
    
class ConversationTurn:
    """Represents a single turn in a conversation."""
    def __init__(self, question: str, response: str, timestamp: datetime, category: str = "general"):
        self.question = question
        self.response = response
        self.timestamp = timestamp
        self.category = category
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'question': self.question,
            'response': self.response,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        return cls(
            question=data['question'],
            response=data['response'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            category=data.get('category', 'general')
        )

class ConversationSession:
    """Manages a single conversation session with memory."""
    def __init__(self, session_id: str = None, max_turns: int = 10):
        self.session_id = session_id or str(uuid.uuid4())
        self.turns: List[ConversationTurn] = []
        self.max_turns = max_turns
        self.created_at = datetime.now()
        self.last_activity = self.created_at
        
    def add_turn(self, question: str, response: str, category: str = "general"):
        """Add a new turn to the conversation."""
        turn = ConversationTurn(question, response, datetime.now(), category)
        self.turns.append(turn)
        self.last_activity = datetime.now()
        
        # Keep only the last max_turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
            
    def get_context(self, turns_back: int = 3) -> str:
        """Get conversation context for ChatGPT."""
        if not self.turns:
            return ""
            
        recent_turns = self.turns[-turns_back:] if turns_back > 0 else self.turns
        context_parts = []
        
        for turn in recent_turns:
            context_parts.append(f"Previous Q: {turn.question}")
            context_parts.append(f"Previous A: {turn.response}")
            
        return "\n".join(context_parts)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'turns': [turn.to_dict() for turn in self.turns],
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        session = cls(session_id=data['session_id'])
        session.turns = [ConversationTurn.from_dict(turn_data) for turn_data in data['turns']]
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        return session

class ConversationManager:
    """Manages conversations, metrics, and Bible study sessions."""
    
    def __init__(self, data_dir: str = "data", max_session_turns: int = 3):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Memory optimization settings
        self.MAX_ACTIVE_SESSIONS = 3  # Limit active sessions
        self.MAX_RECENT_METRICS = 20  # Limit recent metrics storage  
        self.SESSION_TIMEOUT_MINUTES = 20  # Shorter session timeout
        self.MAX_TEXT_LENGTH = 150  # Compress long text
        
        # Lightweight storage files
        self.aggregated_file = self.data_dir / "aggregated_metrics.json"
        self.sessions_file = self.data_dir / "active_sessions.json"  # Only active sessions
        
        # Recent data (will be purged)
        self.recent_metrics: List[ConversationMetrics] = []
        self.aggregated_data: Dict[str, AggregatedMetrics] = {}
        
        # Session management with size limits
        self.current_session: Optional[ConversationSession] = None
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_session_turns = max_session_turns
        
        # Bible keywords for extraction
        self.bible_keywords = {
            'books': ['genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy', 'joshua', 'judges', 
                     'ruth', 'samuel', 'kings', 'chronicles', 'ezra', 'nehemiah', 'esther', 'job', 
                     'psalms', 'proverbs', 'ecclesiastes', 'song', 'isaiah', 'jeremiah', 'lamentations',
                     'ezekiel', 'daniel', 'hosea', 'joel', 'amos', 'obadiah', 'jonah', 'micah', 'nahum',
                     'habakkuk', 'zephaniah', 'haggai', 'zechariah', 'malachi', 'matthew', 'mark', 
                     'luke', 'john', 'acts', 'romans', 'corinthians', 'galatians', 'ephesians',
                     'philippians', 'colossians', 'thessalonians', 'timothy', 'titus', 'philemon',
                     'hebrews', 'james', 'peter', 'jude', 'revelation'],
            'topics': ['faith', 'prayer', 'love', 'hope', 'forgiveness', 'salvation', 'grace', 'mercy',
                      'wisdom', 'peace', 'joy', 'strength', 'guidance', 'trust', 'worship', 'praise',
                      'blessing', 'healing', 'comfort', 'protection', 'provision', 'kingdom', 'heaven',
                      'sin', 'redemption', 'righteousness', 'holiness', 'spirit', 'truth', 'light']
        }
        
        self.load_data()
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract Bible-related keywords from text."""
        text_lower = text.lower()
        keywords = []
        
        # Extract Bible books
        for book in self.bible_keywords['books']:
            if book in text_lower:
                keywords.append(book)
        
        # Extract biblical topics
        for topic in self.bible_keywords['topics']:
            if topic in text_lower:
                keywords.append(topic)
        
        # Extract verse references (e.g., John 3:16, Psalm 23)
        verse_pattern = r'\b([a-zA-Z]+)\s*\d+(?::\d+)?'
        verse_matches = re.findall(verse_pattern, text)
        for match in verse_matches:
            if match.lower() in self.bible_keywords['books']:
                keywords.append(f"{match}_verse")
        
        return list(set(keywords))  # Remove duplicates
    
    def load_data(self):
        """Load existing aggregated data and active sessions."""
        try:
            # Load aggregated metrics (long-term storage)
            if self.aggregated_file.exists():
                with open(self.aggregated_file, 'r') as f:
                    agg_data = json.load(f)
                    self.aggregated_data = {
                        date: AggregatedMetrics(**data) 
                        for date, data in agg_data.items()
                    }
                    
            # Load only active sessions (not expired)
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                    self.sessions = {
                        sid: ConversationSession.from_dict(data) 
                        for sid, data in sessions_data.items()
                    }
                    # Clean up expired sessions on load
                    self.cleanup_expired_sessions()
                    
            logger.info(f"Loaded {len(self.aggregated_data)} days of aggregated metrics and {len(self.sessions)} active sessions")
            
        except Exception as e:
            logger.error(f"Error loading conversation data: {e}")
            
    def save_data(self):
        """Save lightweight data to disk."""
        try:
            # Aggregate today's data if we have recent metrics
            if self.recent_metrics:
                self._aggregate_daily_data()
            
            # Save aggregated metrics (long-term, lightweight)
            agg_data = {date: asdict(metrics) for date, metrics in self.aggregated_data.items()}
            with open(self.aggregated_file, 'w') as f:
                json.dump(agg_data, f, indent=2)
                
            # Save only active sessions (clean up expired ones first)
            self.cleanup_expired_sessions()
            sessions_data = {sid: session.to_dict() for sid, session in self.sessions.items()}
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
                
            logger.debug("Lightweight conversation data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving conversation data: {e}")
    
    def _aggregate_daily_data(self):
        """Aggregate recent metrics into daily summaries and clear recent data."""
        if not self.recent_metrics:
            return
            
        # Group by date
        daily_data = defaultdict(list)
        for metric in self.recent_metrics:
            date = datetime.fromisoformat(metric.timestamp).date().isoformat()
            daily_data[date].append(metric)
        
        # Create aggregated metrics for each day
        for date, day_metrics in daily_data.items():
            if date in self.aggregated_data:
                # Update existing aggregation
                existing = self.aggregated_data[date]
                combined_metrics = day_metrics + []  # Add to existing if needed
            else:
                combined_metrics = day_metrics
            
            # Calculate aggregations
            total_conversations = len(combined_metrics)
            categories = Counter(m.question_category for m in combined_metrics)
            
            # Extract and count keywords
            all_keywords = []
            for metric in combined_metrics:
                keywords = self.extract_keywords(metric.question)
                all_keywords.extend(keywords)
            keyword_counts = Counter(all_keywords)
            
            # Calculate averages
            avg_response_time = sum(m.total_response_time for m in combined_metrics) / total_conversations
            success_rate = sum(1 for m in combined_metrics if m.success) / total_conversations * 100
            
            # Hourly distribution
            hourly_dist = Counter(datetime.fromisoformat(m.timestamp).hour for m in combined_metrics)
            
            # Create or update aggregated metrics
            self.aggregated_data[date] = AggregatedMetrics(
                date=date,
                total_conversations=total_conversations,
                categories=dict(categories),
                keywords=dict(keyword_counts.most_common(20)),  # Keep top 20 keywords
                avg_response_time=round(avg_response_time, 2),
                success_rate=round(success_rate, 1),
                hourly_distribution=dict(hourly_dist)
            )
        
        # Clear recent metrics after aggregation
        self.recent_metrics.clear()
        logger.info(f"Aggregated {len(daily_data)} days of metrics")
            
    def start_session(self, session_type: str = "general") -> str:
        """Start a new conversation session."""
        session = ConversationSession()
        self.current_session = session
        self.sessions[session.session_id] = session
        
        logger.info(f"Started new {session_type} session: {session.session_id}")
        return session.session_id
        
    def get_or_create_session(self) -> ConversationSession:
        """Get current session or create a new one."""
        if not self.current_session or self.current_session.is_expired():
            self.start_session()
        return self.current_session
        
    def categorize_question(self, question: str) -> str:
        """Categorize the question for analytics."""
        question_lower = question.lower()
        
        # Bible-specific categories
        if any(word in question_lower for word in ['verse', 'scripture', 'bible', 'book of']):
            return "bible_verse"
        elif any(word in question_lower for word in ['prayer', 'pray']):
            return "prayer"
        elif any(word in question_lower for word in ['faith', 'believe', 'god', 'jesus', 'christ']):
            return "theology"
        elif any(word in question_lower for word in ['time', 'clock', 'what time']):
            return "time"
        elif any(word in question_lower for word in ['weather']):
            return "weather"
        elif any(word in question_lower for word in ['continue', 'more', 'tell me more', 'explain']):
            return "follow_up"
        else:
            return "general"
            
    def record_conversation(self, question: str, response: str, metrics: Dict[str, float]) -> str:
        """Record a conversation turn with lightweight metrics."""
        session = self.get_or_create_session()
        category = self.categorize_question(question)
        
        # Add to conversation history (limited turns) with compression
        compressed_question = self._compress_text(question)
        compressed_response = self._compress_text(response)
        session.add_turn(compressed_question, compressed_response, category)
        
        # Limit session size to prevent memory bloat
        if len(session.turns) > self.max_session_turns:
            session.turns = session.turns[-self.max_session_turns:]
        
        # Create lightweight metrics record (will be aggregated daily)
        conversation_metrics = ConversationMetrics(
            session_id=session.session_id,
            timestamp=datetime.now().isoformat(),
            question=self._compress_text(question),  # Use compression method
            question_category=category,
            speech_recognition_time=metrics.get('speech_recognition_time', 0.0),
            chatgpt_processing_time=metrics.get('chatgpt_processing_time', 0.0),
            tts_generation_time=metrics.get('tts_generation_time', 0.0),
            total_response_time=sum(metrics.values()),
            response_length=len(response),
            success=True
        )
        
        # Add to recent metrics (will be aggregated and purged)
        self.recent_metrics.append(conversation_metrics)
        
        # Trigger daily aggregation if we have too many recent metrics
        if len(self.recent_metrics) >= self.MAX_RECENT_METRICS:  # Use configurable limit
            self._aggregate_daily_data()
        
        # Periodic cleanup
        if len(self.recent_metrics) % 10 == 0:  # Every 10 conversations
            self._purge_old_data()
            self._cleanup_sessions()  # Add session cleanup
        
        self.save_data()
        
        logger.info(f"Recorded conversation in category '{category}' - Total time: {conversation_metrics.total_response_time:.2f}s")
        return session.session_id
    
    def _purge_old_data(self):
        """Purge data older than 7 days to save space."""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Purge old recent metrics
        self.recent_metrics = [
            m for m in self.recent_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]
        
        # Keep only last 30 days of aggregated data
        cutoff_agg_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        old_dates = [date for date in self.aggregated_data.keys() if date < cutoff_agg_date]
        for date in old_dates:
            del self.aggregated_data[date]
        
        if old_dates:
            logger.info(f"Purged {len(old_dates)} days of old aggregated data")
        
        # Cleanup expired sessions
        self.cleanup_expired_sessions()
        
    def _cleanup_sessions(self):
        """Enhanced session cleanup with memory limits."""
        # Remove expired sessions
        self.cleanup_expired_sessions()
        
        # If we have too many active sessions, remove oldest ones
        if len(self.sessions) > self.MAX_ACTIVE_SESSIONS:
            # Sort sessions by last activity (oldest first)
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_activity
            )
            
            # Remove excess sessions
            excess_count = len(self.sessions) - self.MAX_ACTIVE_SESSIONS
            for session_id, session in sorted_sessions[:excess_count]:
                del self.sessions[session_id]
                logger.info(f"Removed old session {session_id} due to memory limits")
        
        # If current session is expired, clear it
        if (self.current_session and 
            self.current_session.is_expired(self.SESSION_TIMEOUT_MINUTES)):
            self.current_session = None
            
    def _compress_text(self, text: str) -> str:
        """Compress text to save memory."""
        if len(text) <= self.MAX_TEXT_LENGTH:
            return text
        return text[:self.MAX_TEXT_LENGTH] + "..."
        
    def get_conversation_context(self, turns_back: int = 3) -> str:
        """Get conversation context for multi-turn conversations."""
        if not self.current_session:
            return ""
        return self.current_session.get_context(turns_back)
        
    def get_analytics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get conversation analytics from aggregated and recent data."""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).date()
        
        # Combine recent metrics and aggregated data
        total_conversations = 0
        combined_categories = defaultdict(int)
        combined_keywords = defaultdict(int)
        total_response_time = 0
        total_success = 0
        daily_activity = {}
        
        # Add aggregated data
        for date_str, agg_data in self.aggregated_data.items():
            date = datetime.fromisoformat(date_str).date()
            if date >= cutoff_date:
                total_conversations += agg_data.total_conversations
                for cat, count in agg_data.categories.items():
                    combined_categories[cat] += count
                for keyword, count in agg_data.keywords.items():
                    combined_keywords[keyword] += count
                total_response_time += agg_data.avg_response_time * agg_data.total_conversations
                total_success += (agg_data.success_rate / 100) * agg_data.total_conversations
                daily_activity[date_str] = agg_data.total_conversations
        
        # Add recent metrics
        recent_metrics = [
            m for m in self.recent_metrics 
            if datetime.fromisoformat(m.timestamp).date() >= cutoff_date
        ]
        
        if recent_metrics:
            total_conversations += len(recent_metrics)
            for m in recent_metrics:
                combined_categories[m.question_category] += 1
                # Extract keywords from recent questions
                keywords = self.extract_keywords(m.question)
                for keyword in keywords:
                    combined_keywords[keyword] += 1
                total_response_time += m.total_response_time
                if m.success:
                    total_success += 1
                
                # Add to daily activity
                date_str = datetime.fromisoformat(m.timestamp).date().isoformat()
                daily_activity[date_str] = daily_activity.get(date_str, 0) + 1
        
        if total_conversations == 0:
            return self._empty_analytics()
        
        # Calculate averages
        avg_response_time = total_response_time / total_conversations
        success_rate = (total_success / total_conversations) * 100
        
        # Get top keywords and categories
        top_keywords = dict(Counter(combined_keywords).most_common(15))
        top_categories = dict(combined_categories)
        
        return {
            'total_conversations': total_conversations,
            'active_sessions': len([s for s in self.sessions.values() if not s.is_expired()]),
            'question_categories': top_categories,
            'top_keywords': top_keywords,  # New: Bible keywords/topics
            'performance': {
                'avg_response_time': round(avg_response_time, 2),
                'avg_chatgpt_time': round(avg_response_time * 0.7, 2),  # Estimate
                'avg_tts_time': round(avg_response_time * 0.3, 2)  # Estimate
            },
            'daily_activity': daily_activity,
            'success_rate': round(success_rate, 1)
        }
        
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            'total_conversations': 0,
            'active_sessions': 0,
            'question_categories': {},
            'performance': {
                'avg_response_time': 0,
                'avg_chatgpt_time': 0,
                'avg_tts_time': 0
            },
            'popular_questions': [],
            'daily_activity': {},
            'success_rate': 100
        }
        
    def cleanup_expired_sessions(self, timeout_minutes: int = 60):
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items() 
            if session.is_expired(timeout_minutes)
        ]
        
        for sid in expired:
            del self.sessions[sid]
            
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
            
    def get_bible_study_suggestions(self) -> List[str]:
        """Get Bible study suggestions based on conversation history."""
        if not self.current_session or not self.current_session.turns:
            return [
                "What does the Bible say about faith?",
                "Tell me about the book of Psalms",
                "Explain the meaning of John 3:16"
            ]
            
        # Analyze recent topics
        recent_questions = [turn.question for turn in self.current_session.turns[-3:]]
        recent_text = " ".join(recent_questions).lower()
        
        suggestions = []
        
        if "faith" in recent_text:
            suggestions.extend([
                "Tell me more about faith in difficult times",
                "What are examples of faith in the Old Testament?"
            ])
        elif "prayer" in recent_text:
            suggestions.extend([
                "How did Jesus teach us to pray?",
                "What does the Bible say about answered prayer?"
            ])
        elif "love" in recent_text:
            suggestions.extend([
                "Explain 1 Corinthians 13 about love",
                "How does God show His love for us?"
            ])
        else:
            suggestions.extend([
                "Continue our previous discussion",
                "Summarize what we've talked about",
                "What's a related Bible verse?"
            ])
            
        return suggestions[:3]  # Return top 3 suggestions