#!/usr/bin/env python3
"""
Visual Feedback Interface for Bible Clock Voice Assistant
Provides visual state updates for E-ink display integration
"""

import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class VisualFeedback:
    """Visual feedback system for voice assistant states."""
    
    def __init__(self, display_callback: Optional[Callable] = None):
        """Initialize visual feedback system.
        
        Args:
            display_callback: Function to call for actual display updates
        """
        self.display_callback = display_callback
        self.current_state = "ready"
        self.current_message = ""
        self.state_history = []
        
        # State configuration with display properties
        self.state_config = {
            "initializing": {
                "icon": "⚙️",
                "color": "blue",
                "priority": 1,
                "timeout": None
            },
            "ready": {
                "icon": "👂",
                "color": "green", 
                "priority": 0,
                "timeout": None
            },
            "listening": {
                "icon": "🎧",
                "color": "blue",
                "priority": 2,
                "timeout": None
            },
            "wake_detected": {
                "icon": "🎯",
                "color": "yellow",
                "priority": 3,
                "timeout": 2
            },
            "recording": {
                "icon": "🎤",
                "color": "red",
                "priority": 4,
                "timeout": None
            },
            "processing": {
                "icon": "⚡",
                "color": "orange",
                "priority": 5,
                "timeout": None
            },
            "thinking": {
                "icon": "🧠",
                "color": "purple",
                "priority": 6,
                "timeout": None
            },
            "speaking": {
                "icon": "🗣️",
                "color": "green",
                "priority": 7,
                "timeout": None
            },
            "interrupted": {
                "icon": "🔥",
                "color": "red",
                "priority": 8,
                "timeout": 3
            },
            "error": {
                "icon": "❌",
                "color": "red",
                "priority": 9,
                "timeout": 5
            },
            "shutdown": {
                "icon": "🛑",
                "color": "gray",
                "priority": 10,
                "timeout": None
            }
        }
    
    def update_state(self, state: str, message: str = ""):
        """Update the visual state.
        
        Args:
            state: New state identifier
            message: Optional descriptive message
        """
        try:
            if state not in self.state_config:
                logger.warning(f"Unknown visual state: {state}")
                return
            
            # Update internal state
            previous_state = self.current_state
            self.current_state = state
            self.current_message = message
            
            # Add to history
            self.state_history.append({
                'state': state,
                'message': message,
                'timestamp': time.time(),
                'previous_state': previous_state
            })
            
            # Keep only last 10 states
            if len(self.state_history) > 10:
                self.state_history.pop(0)
            
            # Log the state change
            state_info = self.state_config[state]
            logger.info(f"Visual state: {state_info['icon']} {state} - {message}")
            
            # Call display callback if provided
            if self.display_callback:
                try:
                    self.display_callback(state, message, state_info)
                except Exception as e:
                    logger.error(f"Display callback error: {e}")
            
            # Handle automatic state timeouts
            if state_info.get('timeout'):
                import threading
                def auto_return_to_ready():
                    time.sleep(state_info['timeout'])
                    if self.current_state == state:  # Only if state hasn't changed
                        self.update_state("ready", "Voice assistant ready")
                
                threading.Thread(target=auto_return_to_ready, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Visual state update error: {e}")
    
    def get_current_state(self):
        """Get current visual state information."""
        state_info = self.state_config.get(self.current_state, {})
        return {
            'state': self.current_state,
            'message': self.current_message,
            'icon': state_info.get('icon', '?'),
            'color': state_info.get('color', 'black'),
            'priority': state_info.get('priority', 0),
            'timestamp': time.time()
        }
    
    def get_state_history(self):
        """Get recent state history."""
        return self.state_history.copy()
    
    def format_for_display(self, max_width: int = 20) -> dict:
        """Format current state for display on screen.
        
        Args:
            max_width: Maximum width for message text
            
        Returns:
            Dict with formatted display information
        """
        state_info = self.get_current_state()
        
        # Truncate message if too long
        message = state_info['message']
        if len(message) > max_width:
            message = message[:max_width-3] + "..."
        
        return {
            'title': f"{state_info['icon']} {state_info['state'].title()}",
            'message': message,
            'color': state_info['color'],
            'priority': state_info['priority']
        }


class EInkVisualFeedback(VisualFeedback):
    """E-ink display specific visual feedback implementation."""
    
    def __init__(self, eink_display=None):
        """Initialize E-ink visual feedback.
        
        Args:
            eink_display: E-ink display object with update methods
        """
        super().__init__(display_callback=self._update_eink_display)
        self.eink_display = eink_display
        self.last_update_time = 0
        self.min_update_interval = 2  # Minimum seconds between E-ink updates
    
    def _update_eink_display(self, state: str, message: str, state_info: dict):
        """Update E-ink display with current state.
        
        Args:
            state: Current state
            message: State message
            state_info: State configuration
        """
        try:
            # Rate limit E-ink updates to prevent ghosting
            current_time = time.time()
            if current_time - self.last_update_time < self.min_update_interval:
                return
            
            if not self.eink_display:
                return
            
            # Format display info
            display_info = self.format_for_display(max_width=25)
            
            # Update E-ink display
            # This would integrate with actual E-ink display library
            # For now, just log what would be displayed
            logger.info(f"E-ink Update: {display_info['title']}")
            if display_info['message']:
                logger.info(f"E-ink Message: {display_info['message']}")
            
            self.last_update_time = current_time
            
            # Example E-ink integration:
            # self.eink_display.clear()
            # self.eink_display.text(display_info['title'], x=10, y=10, size=16)
            # self.eink_display.text(display_info['message'], x=10, y=30, size=12)
            # self.eink_display.update()
            
        except Exception as e:
            logger.error(f"E-ink display update error: {e}")


def create_visual_feedback_callback(verse_manager=None) -> Callable:
    """Create a visual feedback callback function for voice assistant.
    
    Args:
        verse_manager: Optional verse manager for display integration
        
    Returns:
        Callback function for visual state updates
    """
    # Initialize visual feedback system
    visual_feedback = VisualFeedback()
    
    def visual_callback(state: str, message: str = ""):
        """Visual feedback callback for voice assistant."""
        visual_feedback.update_state(state, message)
        
        # Optional: Update verse display with voice state
        # This could integrate with the main Bible clock display
        if verse_manager and hasattr(verse_manager, 'set_voice_state'):
            verse_manager.set_voice_state(state, message)
    
    return visual_callback


def create_eink_visual_feedback(eink_display=None) -> Callable:
    """Create E-ink specific visual feedback callback.
    
    Args:
        eink_display: E-ink display object
        
    Returns:
        E-ink optimized callback function
    """
    eink_feedback = EInkVisualFeedback(eink_display)
    
    def eink_callback(state: str, message: str = ""):
        """E-ink visual feedback callback."""
        eink_feedback.update_state(state, message)
    
    return eink_callback