#!/bin/bash

# Bible Clock Memory Monitor and Auto-Restart Script
# Monitors memory usage every 2 minutes and restarts if usage exceeds 220MB for 3+ consecutive checks

SCRIPT_DIR="/home/admin/Bible-Clock-v3"
LOG_FILE="/var/log/bible-clock-memory-monitor.log"
MEMORY_THRESHOLD=220  # MB
CHECK_INTERVAL=120    # 2 minutes in seconds
CONSECUTIVE_LIMIT=3   # Number of consecutive high memory readings before restart

# Counter for consecutive high memory readings
consecutive_high_count=0

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

get_bible_clock_memory() {
    # Get memory usage of bible_clock.py process in MB
    local pid=$(pgrep -f "bible_clock.py")
    if [ -z "$pid" ]; then
        echo "0"
        return
    fi
    
    # Get RSS memory in KB and convert to MB
    local memory_kb=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ')
    if [ -z "$memory_kb" ]; then
        echo "0"
    else
        echo $((memory_kb / 1024))
    fi
}

restart_bible_clock() {
    log_message "Restarting Bible Clock due to high memory usage (${consecutive_high_count} consecutive readings above ${MEMORY_THRESHOLD}MB)"
    
    # Stop the service
    sudo systemctl stop bible-clock
    sleep 3
    
    # Start the service
    sudo systemctl start bible-clock
    sleep 5
    
    # Reset counter
    consecutive_high_count=0
    
    log_message "Bible Clock restarted successfully"
}

check_service_running() {
    if ! systemctl is-active --quiet bible-clock; then
        log_message "Bible Clock service is not running - attempting to start"
        sudo systemctl start bible-clock
        sleep 5
    fi
}

# Main monitoring loop
log_message "Memory monitor started - checking every ${CHECK_INTERVAL} seconds"

while true; do
    # Check if service is running
    check_service_running
    
    # Get current memory usage
    current_memory=$(get_bible_clock_memory)
    
    if [ "$current_memory" -gt "$MEMORY_THRESHOLD" ]; then
        consecutive_high_count=$((consecutive_high_count + 1))
        log_message "High memory usage detected: ${current_memory}MB (${consecutive_high_count}/${CONSECUTIVE_LIMIT})"
        
        if [ "$consecutive_high_count" -ge "$CONSECUTIVE_LIMIT" ]; then
            restart_bible_clock
        fi
    else
        if [ "$consecutive_high_count" -gt 0 ]; then
            log_message "Memory usage normal: ${current_memory}MB - resetting counter"
            consecutive_high_count=0
        else
            log_message "Memory usage: ${current_memory}MB"
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done