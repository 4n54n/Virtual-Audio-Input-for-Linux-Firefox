#!/bin/bash
set -e

echo "============== Installing Python Dependencies =============="
sudo apt install -y python3-pip python3-gi

echo "============== Installing GStreamer (minimal audio support) =============="
sudo apt install -y \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good

echo "============== Installing VLC Backend (used by Python-VLC) =============="
sudo apt install -y vlc python3-vlc
#sudo apt install -y libvlc5 libvlc-dev python3-vlc // minimal

echo "============== Installing PulseAudio Requirements =============="
sudo apt install -y pulseaudio pulseaudio-utils

echo "============== Restarting PulseAudio =============="
pulseaudio -k || true
pulseaudio --start

echo "============== Testing Virtual Sink =============="
pactl load-module module-null-sink sink_name=RealtekAudioSink || true

echo "============== DONE =============="
echo "If you saw a number above, virtual sink loaded successfully."
