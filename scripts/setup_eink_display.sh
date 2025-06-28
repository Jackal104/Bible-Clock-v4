#!/bin/bash
set -e
echo "🖥️  Setting up 10.3\" Waveshare E-ink HAT (B) — IT8951..."

# Must be RPi
if ! command -v raspi-config &> /dev/null; then
  echo "❌ Run this on a Raspberry Pi."; exit 1
fi

# Enable SPI
sudo raspi-config nonint do_spi 0
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
  echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
  echo "⚠️ SPI enabled — reboot and re-run." && exit 0
fi

# Dependencies
sudo apt-get update
sudo apt-get install -y build-essential git cmake \
  libfreetype6-dev libjpeg-dev libtiff5-dev zlib1g-dev \
  libopenjp2-7 liblcms2-dev python3-pip python3-venv \
  python3-dev libgpiod-dev bcm2835-doc bcm2835

# Git & build driver
DRIVER_DIR=/home/pi/bible-clock-drivers
mkdir -p "$DRIVER_DIR"
if [ ! -d "$DRIVER_DIR/IT8951-ePaper" ]; then
  git clone https://github.com/waveshare/IT8951-ePaper.git "$DRIVER_DIR/IT8951-ePaper"
fi
cd "$DRIVER_DIR/IT8951-ePaper"
make clean && make epd
cp epd "$DRIVER_DIR/epd"
chmod +x "$DRIVER_DIR/epd"

# DIP switch check
echo "🔧 Ensure HAT SPI switch is on 'SPI' (not USB/I80)."

# VCOM
echo "Using VCOM=-1.21 (from ribbon, your display)"
echo "VCOM_VALUE=-1.21" > "$DRIVER_DIR/vcom.conf"

# GPIO pins (RST & BUSY)
echo "RST=17" >> "$DRIVER_DIR/vcom.conf"
echo "BUSY=24" >> "$DRIVER_DIR/vcom.conf"

# SPI dev
if [ ! -e /dev/spidev0.0 ]; then
  echo "❌ /dev/spidev0.0 missing. Check SPI & cabling."; exit 1
fi

echo ""
echo "✅ Setup complete!"
echo "• DRIVER_PATH=$DRIVER_DIR/epd"
echo "• VCOM=-1.21 V"
echo "• GPIO: RST=17, BUSY=24"
echo ""
echo "Next steps:"
echo "1. In your .env: SIMULATE=0"
echo "2. Ensure .env or config.py points to DRIVER_PATH"
echo "3. Run: python3 run_clock.py --once"
echo "4. If you hit bad refresh quality, adjust VCOM accordingly"