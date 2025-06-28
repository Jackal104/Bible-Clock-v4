"""
Performance monitoring and optimization for Bible Clock.
"""

import psutil
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import deque
import gc

class PerformanceMonitor:
    """Monitor system performance and optimize resource usage."""
    
    def __init__(self, history_size: int = 100):
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        
        # Performance metrics history
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.temperature_history = deque(maxlen=history_size)
        
        # Timing metrics
        self.operation_times = {}
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 30.0):
        """Start performance monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._collect_metrics()
                self._check_thresholds()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self):
        """Collect current performance metrics."""
        timestamp = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_history.append((timestamp, cpu_percent))
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_history.append((timestamp, memory.percent))
        
        # Temperature (Raspberry Pi specific)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = int(f.read().strip())
                temp_celsius = temp_raw / 1000.0
                self.temperature_history.append((timestamp, temp_celsius))
        except (FileNotFoundError, ValueError):
            # Not on Raspberry Pi or thermal info not available
            pass
    
    def _check_thresholds(self):
        """Check performance thresholds and take action."""
        if self.memory_history:
            current_memory = self.memory_history[-1][1]
            if current_memory > 85:
                self.logger.warning(f"High memory usage: {current_memory:.1f}%")
                self._trigger_gc()
        
        if self.temperature_history:
            current_temp = self.temperature_history[-1][1]
            if current_temp > 75:  # 75°C threshold
                self.logger.warning(f"High CPU temperature: {current_temp:.1f}°C")
    
    def _trigger_gc(self):
        """Force garbage collection."""
        before = psutil.virtual_memory().percent
        gc.collect()
        after = psutil.virtual_memory().percent
        self.logger.info(f"Garbage collection: {before:.1f}% -> {after:.1f}% memory")
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        return OperationTimer(self, operation_name)
    
    def record_operation_time(self, operation_name: str, duration: float):
        """Record operation timing."""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = deque(maxlen=50)
        
        self.operation_times[operation_name].append(duration)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'monitoring': self.monitoring
        }
        
        if self.cpu_history:
            cpu_values = [x[1] for x in self.cpu_history]
            summary['cpu'] = {
                'current': cpu_values[-1],
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values)
            }
        
        if self.memory_history:
            memory_values = [x[1] for x in self.memory_history]
            summary['memory'] = {
                'current': memory_values[-1],
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values)
            }
        
        if self.temperature_history:
            temp_values = [x[1] for x in self.temperature_history]
            summary['temperature'] = {
                'current': temp_values[-1],
                'average': sum(temp_values) / len(temp_values),
                'max': max(temp_values)
            }
        
        # Operation timing summary
        timing_summary = {}
        for op_name, times in self.operation_times.items():
            if times:
                timing_summary[op_name] = {
                    'count': len(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        summary['operation_times'] = timing_summary
        
        return summary

class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_operation_time(self.operation_name, duration)