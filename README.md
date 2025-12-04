# 🎤 Virtual Audio Input Injector

A lightweight tool that creates a **virtual microphone** on your system. This virtual audio device appears inside applications like **Firefox**, Google Meet, Zoom, OBS, or any software that accepts microphone input.
It allows you to **select audio files and stream them as microphone input**, so listeners hear the chosen audio instead of (or along with) your real mic.

---

## 📦 How It Works

1. **Start the application** — it automatically creates a virtual microphone device.
2. Open Firefox (or any app) → go to **microphone settings** → choose the virtual device.
3. In the tool UI:

   * Click **Browse** to select audio files
   * Click **Send** to stream the selected audio into the virtual microphone
4. The receiving app will hear the audio as if it came from a real microphone.

---

## 🛠️ Use Cases

* 🔬 Testing audio pipelines
* 📺 Streaming pre-recorded content as microphone input
* 🗣️ Broadcasting announcements or alerts
* 🧪 Development / QA for apps that use microphone input

---

## 🧰 Requirements

* Supported OS:

  * Linux (PipeWire/PulseAudio-based virtual mic)
* Python environment
* Audio playback capability

---

## ▶️ Usage

1. Launch the program
2. Select audio file(s)
3. Click **Send** (or Play)
4. Choose the virtual microphone in Firefox
5. Listeners now hear the audio streamed through the virtual mic
