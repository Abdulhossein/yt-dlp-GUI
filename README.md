# 🎬 YouTube Downloader GUI 🎬

> A full-featured, professional-grade YouTube video downloader with an intuitive graphical interface! 🚀

---

## 🌟 What is This?

This is a **modern, customizable YouTube downloader** built with **Python** and **CustomTkinter** that lets you download videos, playlists, and audio from YouTube with tons of advanced options! 🎵🎥

It's not just some basic downloader - it's packed with features like quality selection, format conversion, subtitle support, sponsorblock integration, and so much more! 💪

---

## ✨ Key Features

### 🎥 Video Downloading
- Download **single videos** or **entire playlists** 🎞️
- Support for **multiple quality levels** (1080p, 720p, 480p, 360p, 240p, and Audio Only) 📺
- **Batch downloading** with queue management 🔄
- Skip or cancel downloads on the fly ⏹️

### 🎵 Audio Extraction
- Extract audio from videos 🎧
- Convert to multiple formats: **MP3, AAC, Opus, WAV** 🎼
- Customizable audio quality (up to 320K) 🔊

### 📥 Format Support
- Download in **MP4, MKV, WebM, AVI, FLV** and more! 📦
- Automatic format conversion with FFmpeg 🔧
- Smart format detection based on quality selection 🎯

### 📝 Subtitles & Metadata
- Download subtitles in **English, Farsi, Arabic** (configurable) 🌍
- Embed subtitles directly into videos 🎬
- Write descriptions and metadata to files 📄
- Thumbnail embedding support 🖼️

### 🚀 Post-Processing Magic
- **SponsorBlock integration** - automatically remove sponsor segments! 🎯
- **FFmpeg post-processing** for remuxing and conversion ⚙️
- Automatic chapter marking ✨

### 🌐 Network Features
- **Proxy support** for bypassing restrictions 🔐
- Configurable socket timeout ⏱️
- Cookie authentication from browser 🍪
- Automatic retries on failure 🔁

### 🗂️ Smart Queue System
- Add multiple videos to download queue 📋
- Queue display shows title, quality, format, and duration ⏱️
- Individual quality/format settings per video 🎛️
- Clear or manage queue easily 🧹

### 💾 Download History
- SQLite database tracks all downloads 🗄️
- View download history with video details 📊
- Track uploader, duration, format, resolution, and file size 📈

### 🎨 User Interface
- **Beautiful dark theme** with CustomTkinter 🌙
- **Responsive design** that scales nicely 📐
- **Live thumbnail preview** of videos 🖼️
- **Real-time progress indicators** 📊
- Playlist video preview with duration 🎞️

### ⚙️ Settings & Configuration
- Full **settings window** for customization ⚙️
- JSON-based configuration for easy tweaking 📋
- Download path customization 📂
- Automatic module dependency management 📦

---

## 🛠️ Installation

### Requirements
- **Python 3.8+** (tested on 3.9+) 🐍
- **Windows 10/11** (fully optimized for Windows) 🪟
- Internet connection 🌐

### Setup (Super Easy!)

1. **Clone or download this repository** 📥
   ```bash
   git clone <repo-url>
   cd youtube_downloader_gui
   ```

2. **Run the program!** It's literally that simple:
   ```bash
   python youtube_downloader.py
   ```

3. The program **automatically handles dependencies** 📦:
   - Installs required packages (CustomTkinter, yt-dlp, Pillow, Requests)
   - Creates necessary directories
   - Sets up the database
   - Generates default config if missing

**That's it! No manual pip install needed!** 🎉

### What Gets Auto-Installed?
- `customtkinter` - Modern UI framework ✨
- `yt-dlp` - Latest YouTube downloader (kept updated!) 🔄
- `requests` - For thumbnail fetching 📸
- `pillow` - Image processing 🎨

---

## 📖 How to Use

### Basic Workflow

1. **Paste a URL** in the input field (YouTube video or playlist link) 🔗
2. **Click "Fetch Info"** to load video/playlist details 🔍
3. **Select quality and format** from dropdown menus 🎛️
4. **Add to Queue** or **Download Now** ⬇️
5. **Watch the progress bar** as it downloads 📊

### Single Video Download

1. Paste video URL (e.g., `https://www.youtube.com/watch?v=abc123xyz`) 🎬
2. Click **"Fetch Info"** button 🔍
3. See video thumbnail and details appear 🖼️
4. Choose:
   - Quality (1080p, 720p, etc.) 📺
   - Format (MP4, MKV, WebM) 📦
   - Audio codec (Best, AAC, MP3, Opus) 🎵
5. Click **"Add to Queue"** or **"Start Download"** ⬇️

### Playlist Download

1. Paste playlist URL (e.g., `https://www.youtube.com/playlist?list=abc123`) 📋
2. Click **"Fetch Info"** button 🔍
3. **Playlist Selector window** pops up showing all videos ✨
4. Check/uncheck videos you want to download ☑️
5. Use **"Select All"** or **"Unselect All"** buttons for quick actions ⚡
6. Click **"Download Selected"** 🚀
7. Videos are added to queue with selected quality settings 🎯

### Queue Management

- **View Queue**: See all pending downloads with details 👀
- **Add to Queue**: Multiple items before downloading 📝
- **Clear Queue**: Remove all items at once 🗑️
- **Start Download**: Process entire queue 🎬
- **Skip Video**: Jump to next item in queue ⏭️
- **Cancel**: Stop all downloads ⛔

### Advanced: Settings Window

Click **⚙️ Settings** to customize:

#### Download Options 📥
- Save path for downloaded files
- Filename template with variables
- Retry attempts for failed downloads
- Concurrent fragment downloads
- Rate limiting (bandwidth throttling)

#### Output Settings 📤
- Keep video after audio extraction
- Write descriptions, annotations, metadata
- Embed thumbnails in files

#### Subtitle Configuration 🌍
- Enable/disable subtitle downloading
- Language selection (add/remove languages)
- Format choice (SRT, VTT, or both)

#### Metadata Control 📋
- Embed video metadata
- Embed thumbnails into videos
- Embed subtitles into videos
- Custom metadata parsing

#### Post-Processing 🔧
- SponsorBlock integration
- Audio extraction settings
- Audio format and quality
- Chapter marking options

#### Network Settings 🌐
- Proxy configuration
- Socket timeout adjustment
- Browser cookie authentication
- Source address binding

---

## ⚙️ Configuration (config.json)

The **config.json** file controls everything! Modify it to customize behavior:

```json
{
  "app": {
    "theme": "dark"  // or "light"
  },
  "download": {
    "save_path": "C:/Users/morad/Desktop/downloads",
    "filename_template": "%(title)s [%(id)s].%(ext)s",
    "retries": 10,
    "fragment_retries": 10,
    "concurrent_fragment_downloads": 5,
    "limit_rate": "0"  // 0 = unlimited bandwidth
  },
  "output": {
    "keep_video": false,
    "writedescription": false,
    "writeinfojson": false,
    "writeannotations": false,
    "writethumbnail": true
  },
  "subtitles": {
    "writesubtitles": true,
    "writeautomaticsub": false,
    "subtitleslangs": ["en", "fa", "ar"],  // Add your languages!
    "subtitlesformat": "srt/vtt"
  },
  "metadata": {
    "embed_metadata": true,
    "embed_thumbnail": true,
    "embed_subtitles": false,
    "parse_metadata": ""
  },
  "post-processing": {
    "use_sponsorblock": true,
    "sponsorblock_mark": ["all"],
    "sponsorblock_remove": ["sponsor"],
    "extract_audio": false,
    "audio_format": "mp3",
    "audio_quality": "192K"
  },
  "network": {
    "use_proxy": false,
    "proxy_url": "",
    "socket_timeout": 20,
    "source_address": "0.0.0.0"
  },
  "authentication": {
    "use_cookies": false,
    "cookie_browser": "chrome"  // or "firefox", "edge"
  }
}
```

### Filename Template Variables 📝
```
%(title)s      - Video title
%(id)s         - YouTube video ID
%(uploader)s   - Channel name
%(ext)s        - File extension
%(duration)s   - Video duration
%(view_count)s - View count
%(upload_date)s- Upload date (YYYYMMDD format)
```

Example template: `[%(uploader)s] %(title)s (%(upload_date)s).%(ext)s`

---

## 🎯 Filename Template Guide

The `filename_template` in config determines how downloaded files are named!

### Common Patterns 📋

**Simple (Title Only)**
```
filename_template: "%(title)s.%(ext)s"
// Result: "My Video Title.mp4"
```

**With ID (Prevents Duplicates)**
```
filename_template: "%(title)s [%(id)s].%(ext)s"
// Result: "My Video Title [abc123xyz].mp4"
```

**With Uploader**
```
filename_template: "[%(uploader)s] %(title)s.%(ext)s"
// Result: "[Channel Name] My Video Title.mp4"
```

**With Date**
```
filename_template: "%(upload_date)s - %(title)s.%(ext)s"
// Result: "20241128 - My Video Title.mp4"
```

**Professional Organization**
```
filename_template: "%(uploader)s/%(upload_date)s - %(title)s.%(ext)s"
// Creates folder per channel!
// Result: "Channel Name/20241128 - My Video Title.mp4"
```

---

## 🗄️ Database

The app uses **SQLite** to track downloads! 📊

### Download History Table
```
- video_id: Unique YouTube ID
- title: Video title
- url: Full YouTube URL
- uploader: Channel name
- duration: Video length in seconds
- format: Download format (mp4, mkv, etc.)
- resolution: Video resolution (1080p, 720p, etc.)
- file_path: Where the file is saved
- file_size: File size in bytes
- download_date: When it was downloaded
- status: Download status (completed, failed, etc.)
```

View your history in the **Download History** tab! 📋

---

## 🐛 Troubleshooting

### "Failed to decrypt with DPAPI" error 🔐
The app **automatically retries without browser cookies** - usually fixes the issue! If it persists:
- Disable browser cookie authentication in settings
- Try a different proxy
- Update yt-dlp (`pip install --upgrade yt-dlp`)

### Video won't download 😞
1. **Check your internet connection** 🌐
2. **Verify the URL is correct** 🔗
3. **Try without proxy** (in settings) 🚫
4. **Update yt-dlp** - YouTube changes constantly!
   ```bash
   pip install --upgrade yt-dlp
   ```
5. **Check if video is private or restricted** 🔒

### Thumbnail won't load 🖼️
- Pillow/PIL might not be installed properly
- Program still works, just won't show thumbnails
- Check internet connection for thumbnail server

### No subtitles downloading 📝
- Make sure language is in the config list
- Check if video has subtitles available
- Enable in settings: `writesubtitles: true`

### Download is slow 🐢
- Check `limit_rate` in config (default is unlimited)
- Reduce `concurrent_fragment_downloads` if unstable
- Close other apps using bandwidth 🌐

### Settings won't save ⚙️
- Make sure `config.json` isn't read-only
- Check file permissions
- Restart the app

---

## 📦 Project Structure

```
youtube_downloader_gui/
├── youtube_downloader.py      # Main application (EVERYTHING HERE!)
├── config.json                # Configuration file
├── downloads.db               # SQLite history database
├── modules/                   # Auto-created for dependencies
│   ├── customtkinter/
│   ├── yt_dlp/
│   ├── PIL/
│   └── requests/
├── dist/                      # Compiled executable (if built)
└── README.md                  # This file! 📄
```

---

## 🔧 Technical Details

### Architecture 🏗️

**Three Main Components:**

1. **YouTubeDownloader Class** 🎬
   - Handles video info extraction with yt-dlp
   - Manages download process and progress tracking
   - Post-processing hooks for FFmpeg operations
   - Download history management via SQLite

2. **MainWindow Class** 🪟
   - CustomTkinter-based GUI
   - Real-time progress display
   - Queue management system
   - Settings interface

3. **Playlist Selector** 📋
   - Popup window for playlist selection
   - Batch video preview
   - Individual video selection

### Dependencies 📚

| Package | Purpose | Version |
|---------|---------|---------|
| `customtkinter` | Modern GUI framework | 0.6.0+ |
| `yt-dlp` | YouTube extractor | Latest |
| `requests` | HTTP requests | Latest |
| `pillow` | Image processing | Latest |
| `sqlite3` | Database (built-in) | - |
| `ffmpeg` | Post-processing | External |

### Threading 🧵
- Downloads run on **separate threads** to keep UI responsive
- Progress callbacks update GUI in real-time
- No UI freezing during long downloads!

### Error Handling 🛡️
- Graceful fallbacks for missing PIL
- Cookie decryption retry mechanism
- Comprehensive error messages
- Retry logic for failed downloads

---

## 🎬 Advanced Examples

### Example 1: Batch Download Channel Videos 🎞️
1. Find playlist from channel
2. Paste playlist URL
3. Click "Fetch Info"
4. Select all videos (or specific ones)
5. Choose quality/format
6. Click "Download Selected"
7. Grab coffee ☕

### Example 2: Convert Videos to MP3 🎵
1. Paste video URL
2. Click "Fetch Info"
3. Select "Audio Only" quality
4. Select "MP3" format
5. Adjust audio quality (192K is good)
6. Download!

### Example 3: Batch with Different Settings 🎛️
1. Add multiple videos to queue
2. Set quality for first video, add to queue
3. Set different quality for second video, add to queue
4. Each item keeps its own settings!
5. Click "Start Download"

---

## 🔐 Security & Privacy

✅ **This app is safe!**
- No trackers or analytics
- Doesn't upload your data anywhere
- Uses open-source yt-dlp library
- All processing is local

### About Browser Cookies 🍪
- Optional feature for accessing private videos
- Only used if you enable it
- Requires your permission and browser password
- Supported: Chrome, Firefox, Edge, Safari

---

## 📊 Performance Tips

### For Faster Downloads 🚀
- Increase `concurrent_fragment_downloads` to 10 (in settings)
- Use wired internet if possible 🔌
- Close background apps 💤
- Disable post-processing if not needed ⚙️

### For Better Stability 🛡️
- Increase `socket_timeout` to 30 (if experiencing timeouts)
- Use proxy if your ISP throttles YouTube
- Keep `fragment_retries` at 10 or higher
- Reduce `concurrent_fragment_downloads` if getting errors

### For Smaller Files 💾
- Select lower quality (480p or 360p)
- Use audio-only for music
- Disable unnecessary metadata
- Choose MP4 format (most efficient)

---

## 🐛 Known Limitations

1. **Requires FFmpeg** for post-processing features
   - Most Windows installs have it already
   - If not, download from ffmpeg.org

2. **Age-restricted videos** may require login
   - Enable browser cookies in settings

3. **Streaming-only videos** (like some livestreams) can't be downloaded

4. **Some private/membership videos** require special access

5. **Regional restrictions** might block some content

---

## 💡 Tips & Tricks

### Pro Tip #1: Organize by Channel 🎨
Use template: `%(uploader)s/%(upload_date)s - %(title)s.%(ext)s`
Creates automatic folder structure by channel name!

### Pro Tip #2: Never Lose History 📚
Download history is automatically saved to `downloads.db`
You can always check what you've downloaded!

### Pro Tip #3: SponsorBlock is Amazing 🎯
Automatically removes sponsor segments from videos!
Enable it in settings and never watch ads again!

### Pro Tip #4: Queue Different Qualities 🎛️
Add same video multiple times with different qualities
Download multiple versions without re-downloading!

### Pro Tip #5: Rate Limiting 🐢
Set `limit_rate` in config to throttle bandwidth
Leave room for other internet usage! 🌐

---

## 🔄 Updating

### Automatic Updates 🔃
yt-dlp updates automatically when YouTube changes!
The app checks for new versions on each run.

### Manual Update 📦
```bash
pip install --upgrade yt-dlp
```

---

## 📝 License

This project is provided as-is for educational and personal use. 📚

---

## 🤝 Contributing

Found a bug? Have a feature request? 🐛✨

1. Test the issue thoroughly
2. Document what's happening
3. Provide steps to reproduce
4. Share your config (without sensitive data)

---

## 🎉 Final Notes

This downloader is **powerful, flexible, and user-friendly**! 🚀

Whether you're downloading a single video or an entire playlist, extracting audio, or converting formats, this tool has you covered! 💪

Enjoy downloading! 🎬📥🎵

---

## 📞 Support

Having issues? 🆘
1. Check the **Troubleshooting** section above
2. Verify your `config.json` is valid
3. Try updating yt-dlp
4. Restart the application
5. Check internet connection

**Happy downloading!** 🎉🎬📥
