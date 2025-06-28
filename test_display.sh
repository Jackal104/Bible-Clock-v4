#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -c "import sys, os; sys.path.insert(0, os.path.join('$SCRIPT_DIR', 'src')); from display_manager import display_manager; display_manager.epd.display(display_manager.image_generator.generate_error_image(), force_refresh=True)"
