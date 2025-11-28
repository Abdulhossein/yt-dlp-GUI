# 🎬 yt-dlp GUI Downloader (PyQt5)

A professional, user-friendly GUI wrapper around [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), built with **PyQt5** for Windows.

---

## 🚀 Features

- ✅ Full access to **all yt-dlp options** via intuitive tabs  
- 🧠 Designed for both **beginners and advanced users**  
- 🖱️ **Hover tooltips** explain each option in plain language  
- 📁 Support for **batch files**, **output templates**, and **subtitles**  
- 🔧 Options grouped in logical tabs:  
  - General, Network, Video Selection  
  - Download, Filesystem, Format  
  - Subtitles, Post-processing, Authentication  
  - Advanced (SponsorBlock, Verbosity, etc.)  
- 📊 **Live download log + progress bar**  
- 🔄 One-click **yt-dlp auto-update**  
- 📂 **Load config files** to restore saved settings

---

## 📦 Requirements

- Python 3.7+  
- PyQt5  
- yt-dlp.exe (placed in the same directory)

Install dependencies:

```bash
pip install pyqt5
```

---

## 🔧 How to Use

1. Paste video URL(s) or load a batch file  
2. Choose desired options across tabs  
3. Click **Download**  
4. Watch progress and status logs in real-time

---

## 🔐 Advanced Options

- Full support for:
  - Proxy, Geo restrictions, Auth credentials
  - SponsorBlock filtering
  - Format selection and merging
  - Post-processing (audio extraction, metadata embedding)

---

## 🧱 Build to EXE (Windows)

Use PyInstaller:

```bash
pyinstaller --onefile --windowed main.py
```

Distribute with:
- `yt-dlp.exe`  
- Optional: `ffmpeg.exe`  

---

## 📘 License

MIT – free for personal and commercial use.
