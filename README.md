# Bible Clock v2.0

A comprehensive Raspberry Pi-based e-ink display system that shows Bible verses corresponding to the current time, featuring a modern web interface, date-based biblical events, and advanced system monitoring.

## ✨ Features

### Core Features
- **Time-Based Verses**: Hour = Chapter, Minute = Verse
- **Date-Based Mode**: Biblical calendar events for special dates
- **Random Mode**: Inspirational verses any time
- **Multiple Translations**: KJV (offline), ESV, NASB, AMP, NIV (online)
- **Book Summaries**: Complete book overviews displayed at minute :00

### Display & Visual
- **E-ink Optimization**: Optimized for 10.3" Waveshare IT8951 displays
- **8 Beautiful Backgrounds**: Automatically cycling background images
- **Font Management**: Multiple fonts with dynamic switching
- **Simulation Mode**: Test without hardware using file output

### Web Interface (NEW in v2.0)
- **Modern Dashboard**: Real-time verse display with live updates
- **Settings Page**: Complete configuration with preview functionality
- **Statistics Page**: Usage analytics with interactive charts
- **RESTful API**: Full API for integration and automation
- **Responsive Design**: Works on desktop, tablet, and mobile

### Advanced Features
- **Enhanced Voice Control**: "Bible Clock" wake word with comprehensive help system
- **ChatGPT Integration**: AI-powered biblical questions and context-aware answers
- **Performance Monitoring**: System health tracking and alerts
- **Error Handling**: Automatic retry logic with graceful fallbacks
- **Advanced Scheduling**: Smart update timing and background tasks
- **Biblical Calendar**: 22 curated events throughout the year

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/Jackal104/Bible-Clockv2.git
cd Bible-Clockv2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your preferences
```

### 2. Run in Different Modes

```bash
# Web interface only (great for testing)
python main.py --web-only

# Full system with display
python main.py

# Simulation mode (no hardware required)
python main.py --simulation

# Debug mode with detailed logging
python main.py --debug --log-file app.log
```

### 3. Access Web Interface

Once running, open your browser to:
- **Local**: http://localhost:5000
- **Network**: http://[your-pi-ip]:5000

## 🌐 Web Interface

### Dashboard
- **Live verse display** with automatic updates
- **System status** monitoring
- **Quick settings** for common changes
- **Display preview** generation
- **Real-time statistics**

### Settings Page
- **Display modes**: Time, Date, or Random
- **Translation selection** with instant preview
- **Background management** with visual selection
- **Font customization** with live preview
- **Advanced system settings**
- **Backup/restore** configuration

### Statistics Page
- **Usage analytics** with interactive charts
- **System performance** monitoring
- **Popular content** tracking
- **Health monitoring** with visual indicators
- **Export functionality** for data analysis

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Display Settings
DISPLAY_WIDTH=1872
DISPLAY_HEIGHT=1404
SIMULATION_MODE=false

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false

# Bible Settings
BIBLE_API_URL=https://bible-api.com
DEFAULT_TRANSLATION=kjv

# Enhanced Voice Control
ENABLE_VOICE=false
WAKE_WORD=bible clock
VOICE_RATE=150
VOICE_VOLUME=0.8

# ChatGPT Integration
OPENAI_API_KEY=your_openai_api_key_here
ENABLE_CHATGPT=false
CHATGPT_MODEL=gpt-3.5-turbo

# ReSpeaker HAT (optional)
RESPEAKER_ENABLED=false
```

### Command Line Options
```bash
python main.py --help

Options:
  --debug              Enable debug logging
  --simulation         Run in simulation mode
  --web-only          Run only web interface
  --disable-voice     Disable voice control
  --disable-web       Disable web interface
  --log-file FILE     Log to specified file
```

## 📅 Biblical Calendar Events

The date mode includes 22 carefully selected biblical events throughout the year:

- **New Year (1/1)**: God's Covenant Renewal
- **Epiphany (1/6)**: Manifestation of Christ
- **Valentine's Day (2/14)**: God's Love
- **Easter Season (4/14)**: Passover/Resurrection
- **Mother's Day (5/8)**: Honoring Mothers
- **Father's Day (6/19)**: Godly Fatherhood
- **Independence Day (7/4)**: Freedom in Christ
- **Thanksgiving (11/25)**: Gratitude to God
- **Christmas (12/25)**: Birth of Christ
- And many more seasonal celebrations!

## 🎙️ Enhanced Voice Control with "Bible Clock" Wake Word

The Bible Clock features comprehensive voice control with an intelligent help system and natural language biblical Q&A.

### Wake Word
All voice commands start with **"Bible Clock"** followed by your request:
- "Bible Clock, help" - Complete command overview
- "Bible Clock, speak verse" - Read current verse
- "Bible Clock, what does this verse mean?" - Ask biblical questions

### Command Categories

#### Display Control
- **"Bible Clock, speak verse"** - Read the current verse aloud
- **"Bible Clock, refresh display"** - Update the display
- **"Bible Clock, change background"** - Switch background style
- **"Bible Clock, cycle mode"** - Change Bible translation
- **"Bible Clock, time mode"** - Switch to time-based verses
- **"Bible Clock, date mode"** - Switch to biblical calendar
- **"Bible Clock, random mode"** - Switch to random verses

#### Information Commands
- **"Bible Clock, what time is it"** - Current time
- **"Bible Clock, system status"** - System health report
- **"Bible Clock, current mode"** - Display mode information
- **"Bible Clock, current verse"** - Verse details and context

#### Biblical Questions (AI Assistant)
Ask any biblical question naturally:
- **"Bible Clock, what does this verse mean?"**
- **"Bible Clock, who was King David?"**
- **"Bible Clock, explain the parable of the prodigal son"**
- **"Bible Clock, what happened in the book of Exodus?"**
- **"Bible Clock, help me understand this passage"**

### Comprehensive Help System
- **"Bible Clock, help"** - Complete overview of all commands
- **"Bible Clock, help display"** - Display control commands
- **"Bible Clock, help questions"** - Biblical Q&A examples
- **"Bible Clock, help setup"** - Configuration assistance

### ReSpeaker HAT Support
For enhanced audio with ReSpeaker HAT:
```bash
# Run the ReSpeaker setup script
chmod +x scripts/setup_respeaker.sh
./scripts/setup_respeaker.sh

# Enable in configuration
echo "RESPEAKER_ENABLED=true" >> .env
```

### Features
- **Context-Aware AI**: Knows current verse for relevant answers
- **Conversation Memory**: Maintains discussion history
- **Natural Language**: Ask questions in plain English
- **Comprehensive Help**: Spoken tutorials for all features
- **Enhanced Audio**: Optimized for ReSpeaker HAT
- **Error Recovery**: Graceful handling of recognition issues

### Example Conversation
```
User: "Bible Clock, help"
System: "Welcome to Bible Clock voice control! I can help you control your Bible Clock display, answer biblical questions, and provide spiritual guidance..."

User: "Bible Clock, what does this verse mean?"
System: "This verse, John 3:16, is often called the 'Gospel in a nutshell' because it beautifully summarizes God's love and salvation plan..."

User: "Bible Clock, change to date mode"
System: "Switched to date-based mode showing biblical calendar events"
```

## 🔌 Hardware Setup

### Required Hardware
- **Raspberry Pi 3B+** or newer (4B recommended)
- **Waveshare 10.3" IT8951** e-ink display
- **MicroSD card** (32GB+ recommended)
- **Power supply** (3A+ for Pi 4)
- **Optional**: USB microphone for voice control

### Display Connection
1. Connect IT8951 HAT to Raspberry Pi GPIO pins
2. Enable SPI interface:
```bash
sudo raspi-config
# Interface Options > SPI > Enable
sudo reboot
```

### System Service Installation
```bash
# Install as system service
sudo cp systemd/bible-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bible-clock
sudo systemctl start bible-clock

# View logs
sudo journalctl -u bible-clock -f
```

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Web dashboard
- `GET /settings` - Settings page
- `GET /statistics` - Statistics page
- `GET /health` - Health check

### API Endpoints
- `GET /api/verse` - Current verse data
- `GET /api/status` - System status
- `GET /api/settings` - Configuration
- `POST /api/settings` - Update settings
- `GET /api/statistics` - Usage statistics
- `POST /api/refresh` - Force display refresh
- `POST /api/preview` - Generate preview

### Example API Response
```json
{
  "success": true,
  "data": {
    "reference": "John 3:16",
    "text": "For God so loved the world...",
    "book": "John",
    "chapter": 3,
    "verse": 16,
    "timestamp": "2024-12-17T10:30:00",
    "is_date_event": false,
    "display_mode": "time"
  }
}
```

## 📂 Project Structure

```
bible-clock/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── README.md              # This file
│
├── src/                   # Core application modules
│   ├── verse_manager.py   # Bible verse logic with date mode
│   ├── image_generator.py # Image creation with font management
│   ├── display_manager.py # E-ink display control
│   ├── service_manager.py # Main service orchestration
│   ├── voice_control.py   # Voice command processing
│   ├── scheduler.py       # Advanced task scheduling
│   ├── performance_monitor.py # System monitoring
│   ├── error_handler.py   # Error handling & retry logic
│   ├── config_validator.py # Configuration validation
│   ├── display_constants.py # E-ink display constants
│   └── web_interface/     # Web interface components
│       ├── app.py         # Flask application
│       ├── templates/     # HTML templates
│       │   ├── base.html  # Base template
│       │   ├── dashboard.html # Main dashboard
│       │   ├── settings.html  # Settings page
│       │   └── statistics.html # Statistics page
│       └── static/        # CSS, JS, images
│           ├── css/style.css  # Custom styles
│           └── js/app.js      # JavaScript application
│
├── data/                  # Application data
│   ├── biblical_calendar.json # Date-based events
│   ├── fallback_verses.json  # Offline verse backup
│   ├── book_summaries.json   # Bible book descriptions
│   ├── translations/         # Bible translation files
│   │   └── bible_kjv.json   # Complete KJV Bible
│   └── fonts/               # TrueType fonts
│
├── images/               # Background images
├── scripts/             # Utility scripts
└── systemd/            # Service configuration
    └── bible-clock.service
```

## 🔧 Troubleshooting

### Web Interface Issues
```bash
# Check if web server is running
curl http://localhost:5000/health

# View web interface logs
python main.py --debug --web-only

# Test API endpoints
curl http://localhost:5000/api/verse
```

### Display Issues
```bash
# Verify SPI is enabled
lsmod | grep spi

# Test in simulation mode
python main.py --simulation --debug

# Check display connections and power
```

### Memory/Performance Issues
```bash
# Monitor system resources
htop

# Check application memory usage
python main.py --debug | grep memory

# View performance statistics via web interface
curl http://localhost:5000/api/statistics
```

### Voice Control Issues
```bash
# Test microphone
arecord -l

# Test speech recognition
python -c "import speech_recognition; print('OK')"

# Run without voice control
python main.py --disable-voice
```

## 🧪 Development & Testing

### Testing Setup
```bash
# Run all tests
pytest tests/

# Test web interface
python main.py --web-only --debug

# Test specific components
python -m src.verse_manager
python -m src.image_generator
```

### Adding Custom Content
- **Backgrounds**: Add 1872x1404 PNG files to `images/`
- **Fonts**: Add TTF files to `data/fonts/`
- **Events**: Edit `data/biblical_calendar.json`
- **Verses**: Modify `data/fallback_verses.json`

## 📈 Performance Specifications

- **Memory Usage**: ~200MB typical, ~300MB peak
- **Display Update**: 2-3 seconds full refresh, <1 second partial
- **Web Response**: <100ms for API calls
- **Storage**: ~100MB total application size
- **Network**: Minimal usage, offline-capable

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Test in simulation mode first
- Ensure web interface remains responsive
- Add tests for new features
- Update documentation as needed
- Follow existing code style

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Waveshare** for excellent e-ink display hardware
- **Bible API providers** for verse access
- **Open source community** for libraries and inspiration
- **Biblical scholars** for translation work
- **Contributors** who help improve this project

## 🆕 What's New in v2.0

- **Complete web interface** with modern UI
- **Date-based biblical calendar** system
- **Advanced statistics** and monitoring
- **Font management** system
- **Enhanced error handling** and retry logic
- **Performance monitoring** with health checks
- **Responsive design** for all devices
- **Configuration management** with preview
- **Export/import** functionality
- **Real-time updates** and notifications

---

*"Thy word is a lamp unto my feet, and a light unto my path." - Psalm 119:105*

**Bible Clock v2.0** - Bringing God's Word to your daily life through technology. 🙏