"""
Main service manager for the Bible Clock application.
"""

import os
import time
import logging
import schedule
import threading
import psutil
from datetime import datetime, timedelta
from typing import Optional

from error_handler import error_handler
from config_validator import ConfigValidator
from scheduler import AdvancedScheduler
from performance_monitor import PerformanceMonitor

class ServiceManager:
    def __init__(self, verse_manager, image_generator, display_manager, voice_control=None, web_interface=None):
        self.verse_manager = verse_manager
        self.image_generator = image_generator
        self.display_manager = display_manager
        self.voice_control = voice_control
        self.web_interface = web_interface
        
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.last_update = None
        self.error_count = 0
        self.max_errors = 10
        
        # Health monitoring settings
        self.memory_threshold = int(os.getenv('MEMORY_THRESHOLD', '80'))
        self.gc_interval = int(os.getenv('GC_INTERVAL', '300'))
        
        # Initialize new components
        self.config_validator = ConfigValidator()
        self.scheduler = AdvancedScheduler()
        self.performance_monitor = PerformanceMonitor()
        
        # Validate configuration on startup
        if not self.config_validator.validate_all():
            report = self.config_validator.get_report()
            for error in report['errors']:
                self.logger.error(f"Configuration error: {error}") 
            for warning in report['warnings']:
                self.logger.warning(f"Configuration warning: {warning}")
            if report['errors']:  # Only fail on errors, not warnings
                raise RuntimeError("Configuration validation failed")
        
        # Schedule verse updates
        self._schedule_updates()
    
    def _schedule_updates(self):
        """Schedule regular verse updates using advanced scheduler."""
        # Use advanced scheduler for verse updates
        self.scheduler.schedule_verse_updates(self._update_verse)
        
        # Schedule background cycling
        self.scheduler.schedule_background_cycling(self._cycle_background, interval_hours=4)
        
        # Schedule maintenance tasks
        self.scheduler.schedule_maintenance(self._daily_maintenance)
        
        # Schedule performance monitoring
        self.scheduler.schedule_custom('health_check', 'every_5_minutes', self._health_check)
        self.scheduler.schedule_custom('garbage_collect', f'every_{self.gc_interval//60}_minutes', self._garbage_collect)
        self.scheduler.schedule_custom('force_refresh', 'hourly', self._force_refresh)
        
        self.logger.info("Advanced update schedule configured")
    
    def run(self):
        """Main service loop."""
        self.running = True
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        # Start advanced scheduler
        self.scheduler.start()
        
        # Start web interface FIRST (before voice control blocks)
        if self.web_interface:
            self._start_web_interface()
        
        # Start voice control if available (runs in blocking mode)
        if self.voice_control:
            self.voice_control.run_main_loop()
        elif os.getenv('ENABLE_VOICE', 'false').lower() == 'true':
            # Try to initialize voice control if enabled but not provided
            try:
                from voice_control import BibleClockVoiceControl
                self.voice_control = BibleClockVoiceControl(
                    self.verse_manager, self.image_generator, self.display_manager
                )
                if self.voice_control.enabled:
                    self.voice_control.run_main_loop()
                    self.logger.info("Voice control auto-initialized")
            except Exception as e:
                self.logger.error(f"Voice control auto-initialization failed: {e}")
        
        # Initial verse display
        self._update_verse()
        
        self.logger.info("Bible Clock service started")
        
        try:
            while self.running:
                # The advanced scheduler runs in its own thread
                # Just keep the main thread alive
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Service interrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service."""
        self.running = False
        
        # Stop all components
        self.scheduler.stop()
        self.performance_monitor.stop_monitoring()
        
        if self.voice_control:
            self.voice_control.stop_listening()
        
        if self.web_interface:
            self._stop_web_interface()
        
        self.logger.info("Bible Clock service stopped")
    
    @error_handler.with_retry(max_retries=2)
    def _update_verse(self):
        """Update the displayed verse at precise minute boundaries."""
        now = datetime.now()
        
        # Only update if we're at the start of a minute (0-2 seconds)
        if now.second <= 2:
            with self.performance_monitor.time_operation('verse_update'):
                # Get current verse
                verse_data = self.verse_manager.get_current_verse()
                
                # Generate image
                image = self.image_generator.create_verse_image(verse_data)
                
                # Display image
                self.display_manager.display_image(image)
                
                # Update tracking
                self.last_update = datetime.now()
                self.error_count = 0
                
                self.logger.info(f"Verse updated: {verse_data['reference']} at {now.strftime('%H:%M:%S')}")
        else:
            self.logger.debug(f"Skipping verse update at {now.strftime('%H:%M:%S')} - not at minute boundary")
    
    def _health_check(self):
        """Perform system health checks."""
        try:
            # Check memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self.memory_threshold:
                self.logger.warning(f"High memory usage: {memory_percent}%")
            
            # Check last update time
            if self.last_update:
                time_since_update = datetime.now() - self.last_update
                if time_since_update > timedelta(minutes=5):
                    self.logger.warning(f"No updates for {time_since_update}")
            
            # Check error rate
            if self.error_count > 5:
                self.logger.warning(f"High error count: {self.error_count}")
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            if disk_percent > 90:
                self.logger.warning(f"Low disk space: {disk_percent:.1f}% used")
            
            self.logger.debug("Health check completed")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    def _garbage_collect(self):
        """Force garbage collection to free memory."""
        try:
            import gc
            before = psutil.virtual_memory().percent
            gc.collect()
            after = psutil.virtual_memory().percent
            
            if before - after > 1:  # Only log if significant reduction
                self.logger.info(f"Garbage collection: {before:.1f}% -> {after:.1f}% memory")
            
        except Exception as e:
            self.logger.error(f"Garbage collection failed: {e}")
    
    def _force_refresh(self):
        """Force a full display refresh to prevent ghosting."""
        try:
            self.logger.info("Performing scheduled full refresh")
            verse_data = self.verse_manager.get_current_verse()
            image = self.image_generator.create_verse_image(verse_data)
            self.display_manager.display_image(image, force_refresh=True)
        except Exception as e:
            self.logger.error(f"Force refresh failed: {e}")
    
    def _cycle_background(self):
        """Automatically cycle background image."""
        try:
            self.image_generator.cycle_background()
            self.logger.info("Background automatically cycled")
        except Exception as e:
            self.logger.error(f"Background cycling failed: {e}")
    
    def _daily_maintenance(self):
        """Perform daily maintenance tasks."""
        try:
            self.logger.info("Starting daily maintenance")
            
            # Force garbage collection
            self._garbage_collect()
            
            # Clear old log entries if needed
            # Add any other maintenance tasks here
            
            self.logger.info("Daily maintenance completed")
        except Exception as e:
            self.logger.error(f"Daily maintenance failed: {e}")
    
    def _start_web_interface(self):
        """Start the web interface in a separate thread."""
        try:
            import threading
            from web_interface.app import create_app
            
            # Create Flask app with all components
            app = create_app(
                verse_manager=self.verse_manager,
                image_generator=self.image_generator,
                display_manager=self.display_manager,
                service_manager=self,
                performance_monitor=self.performance_monitor
            )
            
            # Get web interface configuration
            display_host = os.getenv('WEB_HOST', 'bible-clock')
            bind_host = '0.0.0.0'  # Flask must bind to IP, not hostname
            port = int(os.getenv('WEB_PORT', '5000'))
            debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
            
            # Start Flask app in a separate thread
            def run_web_interface():
                app.run(host=bind_host, port=port, debug=debug, use_reloader=False)
            
            self.web_thread = threading.Thread(target=run_web_interface, daemon=True)
            self.web_thread.start()
            
            self.logger.info(f"Web interface started on http://{display_host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start web interface: {e}")
    
    def _stop_web_interface(self):
        """Stop the web interface."""
        try:
            # Flask server will stop when the main thread exits
            # since we're using daemon threads
            if hasattr(self, 'web_thread') and self.web_thread.is_alive():
                self.logger.info("Web interface stopping...")
        except Exception as e:
            self.logger.error(f"Error stopping web interface: {e}")
    
    def get_status(self) -> dict:
        """Get current service status."""
        status = {
            'running': self.running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'error_count': self.error_count,
            'memory_usage': psutil.virtual_memory().percent,
            'display_info': self.display_manager.get_display_info(),
            'background_info': self.image_generator.get_current_background_info(),
            'scheduler_jobs': self.scheduler.get_job_status(),
            'performance_summary': self.performance_monitor.get_performance_summary()
        }
        
        # Add configuration validation report
        config_report = self.config_validator.get_report()
        status['configuration'] = config_report
        
        return status