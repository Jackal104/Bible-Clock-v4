"""
Display mode constants for IT8951 e-ink displays.
"""

class DisplayModes:
    """E-ink display refresh modes."""
    INIT = 0    # Clear screen
    DU = 1      # Direct update - fastest, 1-bit
    GC16 = 2    # Grayscale clear - highest quality, 16 levels
    GL16 = 3    # Grayscale live - fast grayscale
    GLR16 = 4   # Grayscale live red - for red displays
    GLD16 = 5   # Grayscale live dark - for dark content
    A2 = 6      # Animation mode - very fast
    DU4 = 7     # 4-level direct update

class WaveformModes:
    """Waveform modes for different update types."""
    FULL = 'GC16'     # Full refresh for best quality
    PARTIAL = 'DU'    # Partial refresh for speed
    FAST = 'A2'       # Fastest animation mode