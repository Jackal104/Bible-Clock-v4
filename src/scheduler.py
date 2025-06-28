"""
Advanced scheduling system for Bible Clock.
"""

import schedule
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional

class AdvancedScheduler:
    """Enhanced scheduler with more sophisticated timing options."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.jobs = {}
        self.running = False
        self.thread = None
    
    def schedule_verse_updates(self, callback: Callable):
        """Schedule verse updates with smart timing."""
        # Main update at start of each minute
        job = schedule.every().minute.at(":00").do(callback)
        self.jobs['verse_update'] = job
        
        # Also update at 30 seconds for book summaries (minute 0)
        def smart_update():
            now = datetime.now()
            if now.minute == 0 and now.second >= 30:
                callback()
        
        job = schedule.every(30).seconds.do(smart_update)
        self.jobs['smart_update'] = job
    
    def schedule_background_cycling(self, callback: Callable, interval_hours: int = 4):
        """Schedule automatic background cycling."""
        job = schedule.every(interval_hours).hours.do(callback)
        self.jobs['background_cycle'] = job
    
    def schedule_maintenance(self, callback: Callable):
        """Schedule maintenance tasks."""
        # Daily maintenance at 3 AM
        job = schedule.every().day.at("03:00").do(callback)
        self.jobs['daily_maintenance'] = job
    
    def schedule_custom(self, name: str, when: str, callback: Callable, **kwargs):
        """Schedule custom job."""
        if when == 'hourly':
            job = schedule.every().hour.do(callback, **kwargs)
        elif when == 'daily':
            job = schedule.every().day.do(callback, **kwargs)
        elif when.startswith('every_'):
            # Format: every_30_minutes, every_2_hours
            parts = when.split('_')
            if len(parts) == 3:
                interval = int(parts[1])
                unit = parts[2]
                if unit == 'minutes':
                    job = schedule.every(interval).minutes.do(callback, **kwargs)
                elif unit == 'hours':
                    job = schedule.every(interval).hours.do(callback, **kwargs)
                else:
                    raise ValueError(f"Unsupported time unit: {unit}")
            else:
                raise ValueError(f"Invalid schedule format: {when}")
        else:
            raise ValueError(f"Unsupported schedule type: {when}")
        
        self.jobs[name] = job
        self.logger.info(f"Scheduled job '{name}' for {when}")
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("Advanced scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info("Advanced scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)  # Wait before retrying
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        status = {}
        for name, job in self.jobs.items():
            status[name] = {
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'last_run': getattr(job, 'last_run', None),
                'job_func': job.job_func.__name__ if job.job_func else None
            }
        return status