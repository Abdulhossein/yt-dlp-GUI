# -*- coding: utf-8 -*-

# ============================================================================
# INTEGRATED MODULE MANAGER - EMBEDDED INTO MAIN FILE
# ============================================================================

import sys
import os
import subprocess
import site
from pathlib import Path

# Configuration
MODULES_DIR = Path(__file__).parent / "modules"
REQUIREMENTS = {
    "customtkinter": "0.6.0",
    "yt-dlp": "latest",
    "requests": "latest",
    "pillow": "latest",
}

def ensure_modules_dir():
    """Create modules directory if it doesn't exist."""
    MODULES_DIR.mkdir(exist_ok=True)

def get_installed_version(package_name):
    """Get the installed version of a package."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return None

def install_module(package_name, version="latest"):
    """Install a module to the modules directory."""
    ensure_modules_dir()
    print(f"Installing {package_name}...")
    try:
        if version == "latest":
            spec = package_name
        else:
            spec = f"{package_name}=={version}"
        
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--upgrade",
            "--no-cache-dir",
            spec
        ]
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Warning: Installation of {package_name} had issues:")
            print(result.stderr)
            return False
        print(f"[OK] {package_name} installed successfully")
        return True
    except Exception as e:
        print(f"Error installing {package_name}: {e}")
        return False

def check_and_install_modules():
    """Check all required modules and install if missing."""
    ensure_modules_dir()
    
    print("Checking required modules...")
    missing_modules = []
    
    for module, version in REQUIREMENTS.items():
        module_name = module.replace("-", "_")
        # Special case for pillow - check for PIL import
        if module == "pillow":
            try:
                __import__("PIL")
                print(f"[OK] {module} found in system Python")
                continue
            except ImportError:
                pass
        else:
            # Check if module is already in system Python
            try:
                __import__(module_name)
                print(f"[OK] {module} found in system Python")
                continue
            except ImportError:
                pass
        
        # Check if module is in modules directory (append to path to prioritize system packages)
        try:
            if str(MODULES_DIR) not in sys.path:
                sys.path.append(str(MODULES_DIR))
            if module == "pillow":
                __import__("PIL")
            else:
                __import__(module_name)
            print(f"[OK] {module} found in modules directory")
        except ImportError:
            print(f"[FAIL] {module} not found")
            missing_modules.append((module, version))
    
    # Install missing modules
    if missing_modules:
        print(f"\nInstalling {len(missing_modules)} missing module(s)...")
        for module, version in missing_modules:
            install_module(module, version)
    
    # Ensure modules directory is in path (at the end for fallback)
    if str(MODULES_DIR) not in sys.path:
        sys.path.append(str(MODULES_DIR))

# Run module check and installation
check_and_install_modules()

# ============================================================================
# MAIN IMPORTS
# ============================================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter
import threading
import yt_dlp
import sqlite3
import json
import time
import requests
from io import BytesIO
import webbrowser

# Handle PIL import gracefully - try multiple import methods
Image = None
ImageTk = None

# Try direct PIL import
try:
    from PIL import Image
    print("[OK] PIL (Image) imported successfully")
except ImportError as e:
    print(f"Warning: PIL/Pillow import failed: {e}. Trying alternative imports...")
    try:
        import PIL.Image as Image
        print("[OK] PIL imported via PIL.Image")
    except ImportError as e2:
        print(f"Warning: PIL/Pillow not available: {e2}. Thumbnails will not load.")
        Image = None

# A comprehensive set of default yt-dlp settings.
DEFAULT_CONFIG = {
    "app": {"theme": "dark"},
    "download": {
        "save_path": str(Path.home() / "Downloads" / "YouTube"),
        "filename_template": "%(title)s [%(id)s].%(ext)s",
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 5,
        "limit_rate": "0"  # 0 = unlimited
    },
    "output": {
        "keep_video": False,
        "writedescription": False,
        "writeinfojson": False,
        "writeannotations": False,
        "writethumbnail": True
    },
    "subtitles": {
        "writesubtitles": True,
        "writeautomaticsub": False,
        "subtitleslangs": ["en", "fa", "ar"],
        "subtitlesformat": "srt/vtt"
    },
    "metadata": {
        "embed_metadata": True,
        "embed_thumbnail": True,
        "embed_subtitles": False,
        "parse_metadata": ""
    },
    "post-processing": {
        "use_sponsorblock": True,
        "sponsorblock_mark": ["all"],
        "sponsorblock_remove": ["sponsor"],
        "extract_audio": False,
        "audio_format": "mp3",
        "audio_quality": "192K"
    },
    "network": {
        "use_proxy": False,
        "proxy_url": "",
        "socket_timeout": 20,
        "source_address": "0.0.0.0"  # 0.0.0.0 for auto-select
    },
    "authentication": {
        "use_cookies": False,
        "cookie_browser": "chrome",
        "cookie_file_path": "",
        "use_custom_headers": False,
        "custom_header_type": "Desktop",
        "use_headers_from_cookies": False
    }
}


class EntryContextMenu:
    """Creates a right-click context menu for CTkEntry widgets."""

    def __init__(self, widget):
        self.widget = widget
        self.menu = tkinter.Menu(widget, tearoff=0)
        self.menu.add_command(label="Cut", command=self.cut)
        self.menu.add_command(label="Copy", command=self.copy)
        self.menu.add_command(label="Paste", command=self.paste)

        # Bind the right-click event
        self.widget.bind("<Button-3>" if sys.platform !=
                         "darwin" else "<Button-2>", self.show_menu)

    def show_menu(self, event):
        """Show the context menu."""
        # Enable/disable menu items based on widget state
        try:
            has_selection = bool(self.widget.selection_get())
        except tkinter.TclError:
            has_selection = False

        try:
            can_paste = bool(self.widget.clipboard_get())
        except (tkinter.TclError, ValueError):
            can_paste = False

        self.menu.entryconfig(
            "Cut", state="normal" if has_selection else "disabled")
        self.menu.entryconfig(
            "Copy", state="normal" if has_selection else "disabled")
        self.menu.entryconfig(
            "Paste", state="normal" if can_paste else "disabled")

        self.menu.tk_popup(event.x_root, event.y_root)

    def cut(self):
        try:
            text = self.widget.selection_get()
            self.widget.clipboard_clear()
            self.widget.clipboard_append(text)
            self.widget.delete("sel.first", "sel.last")
        except tkinter.TclError:
            pass
    
    def copy(self):
        try:
            text = self.widget.selection_get()
            self.widget.clipboard_clear()
            self.widget.clipboard_append(text)
        except tkinter.TclError:
            pass
    
    def paste(self):
        try:
            text = self.widget.clipboard_get()
            try:
                self.widget.delete("sel.first", "sel.last")
            except tkinter.TclError:
                pass
            self.widget.insert("insert", text)
        except tkinter.TclError:
            pass


class DatabaseManager:
    """Database manager for download history"""

    def __init__(self, db_path='downloads.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT UNIQUE NOT NULL, title TEXT, url TEXT, uploader TEXT, duration INTEGER, format TEXT, resolution TEXT, file_path TEXT, file_size INTEGER, download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'completed')''')
        self.conn.commit()

    def add_download(self, info):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO downloads (video_id, title, url, uploader, duration, format, resolution, file_path, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (info.get('id'), info.get('title'), info.get(
            'webpage_url'), info.get('uploader'), info.get('duration'), info.get('format'), info.get('resolution'), info.get('_filename') or info.get('requested_downloads', [{}])[0].get('_filename'), info.get('filesize') or info.get('filesize_approx')))
        self.conn.commit()


class YouTubeDownloader:
    """Main class for managing YouTube downloads"""
    
    # Custom User-Agent headers for different device types
    CUSTOM_HEADERS = {
        "Desktop": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        },
        "Android": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        },
        "iOS": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        },
        "TV": {
            "User-Agent": "Mozilla/5.0 (CrKey armv7l 1.54.110279) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        },
        "Chrome": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        },
        "Firefox": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        },
        "Safari": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        },
        "Edge": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
        },
        "Samsung Smart TV": {
            "User-Agent": "Mozilla/5.0 (SmartTV; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/16.0 Chrome/96.0.4664.45 TV Safari/537.36"
        },
        "Roku": {
            "User-Agent": "Mozilla/5.0 (Roku/DVP-7.70 (297.70E04154A)) Gecko/20100101 Firefox/108.0"
        }
    }

    def __init__(self, config_path='config.json', progress_callback=None, postprocessor_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.postprocessor_callback = postprocessor_callback
        self.log_callback = log_callback
        self.config = self.load_config(config_path)
        self.db = DatabaseManager('downloads.db')

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config = DEFAULT_CONFIG.copy()
                for key, value in user_config.items():
                    if key in config and isinstance(value, dict):
                        config[key].update(value)
                    else:
                        config[key] = value
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            self.log(
                f"'{path}' not found or invalid, creating default config.")
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
                return DEFAULT_CONFIG
            except Exception as e:
                self.log(f"Error creating config file: {e}")
                return DEFAULT_CONFIG

    def get_video_info(self, url):
        ydl_opts = {'quiet': True, 'no_warnings': True,
                    'extract_flat': False, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'thumbnail': info.get('thumbnail'),
                'formats': self._parse_formats(info.get('formats', [])),
                'subtitles': list(info.get('subtitles', {}).keys()),
                'views': info.get('view_count'),
                'likes': info.get('like_count'),
                'upload_date': info.get('upload_date'),
                'description': info.get('description'),
                'tags': info.get('tags', []),
                'categories': info.get('categories', []),
                'age_limit': info.get('age_limit'),
                'availability': info.get('availability'),
                'is_live': info.get('is_live', False),
                'channel_id': info.get('channel_id'),
            }
    
    def get_playlist_info(self, url):
        """Extract playlist information with flat extraction."""
        ydl_opts = {'quiet': True, 'no_warnings': True,
                    'extract_flat': 'in_playlist', 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [])
            videos = []
            for entry in entries:
                videos.append({
                    'id': entry.get('id'),
                    'title': entry.get('title', 'Unknown'),
                    'duration': entry.get('duration', 0),
                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                })
            return {
                'title': info.get('title', 'Playlist'),
                'uploader': info.get('uploader', 'N/A'),
                'videos': videos
            }

    def _parse_formats(self, formats):
        video_formats = []
        audio_formats = []
        container_formats = set()
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                video_formats.append({'format_id': f.get('format_id'), 'resolution': f.get('resolution'), 'fps': f.get('fps'), 'vcodec': f.get(
                    'vcodec'), 'filesize': f.get('filesize') or f.get('filesize_approx'), 'format_note': f.get('format_note'), 'ext': f.get('ext')})
            elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                audio_formats.append({'format_id': f.get('format_id'), 'acodec': f.get('acodec'), 'abr': f.get('abr'), 'filesize': f.get('filesize') or f.get('filesize_approx')})
            # Collect all available container formats
            if f.get('ext'):
                container_formats.add(f.get('ext'))
        return {'video': video_formats, 'audio': audio_formats, 'formats': sorted(list(container_formats))}

    def download(self, url, options):
        options['progress_hooks'] = [self.progress_hook]
        options['postprocessor_hooks'] = [self.postprocessor_hook]
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                self.log(f"Attempting to download {url} with specified options.")
                info = ydl.extract_info(url, download=True)
                final_info = ydl.sanitize_info(info)
                self.db.add_download(final_info)
                return {'status': 'success', 'info': final_info}
        except yt_dlp.utils.DownloadError as e:
            if "Failed to decrypt with DPAPI" in str(e) and options.get('cookiesfrombrowser'):
                self.log("Cookie decryption failed. Retrying download without browser cookies.")
                
                new_options = options.copy()
                new_options['cookiesfrombrowser'] = None
                
                try:
                    with yt_dlp.YoutubeDL(new_options) as ydl:
                        self.log(f"Retrying download for {url} without cookies.")
                        info = ydl.extract_info(url, download=True)
                        final_info = ydl.sanitize_info(info)
                        self.db.add_download(final_info)
                        self.log("Download succeeded on retry.")
                        return {'status': 'success', 'info': final_info}
                except Exception as retry_e:
                    self.log(f"Download retry failed: {retry_e}")
                    message = "Cookie decryption failed and the download was unsuccessful without cookies. The video may be private or require a login that is not accessible."
                    return {'status': 'error', 'message': message}
            else:
                import traceback
                traceback.print_exc()
                self.log(f"Download Error: {e}")
                return {'status': 'error', 'message': str(e)}
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log(f"An unexpected error occurred during download: {e}")
            return {'status': 'error', 'message': str(e)}

    def progress_hook(self, d):
        if self.progress_callback:
            self.progress_callback(d)

    def postprocessor_hook(self, d):
        if self.postprocessor_callback:
            self.postprocessor_callback(d)
    
    def extract_headers_from_cookies(self, cookie_file_path):
        """Extract useful headers from cookie file."""
        try:
            with open(cookie_file_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            headers = {}
            if isinstance(cookies, list):
                # Extract security cookies if available
                for cookie in cookies:
                    if cookie.get('name') in ['PSID', 'SSID', 'APISID', 'SAPISID']:
                        headers[f"X-{cookie['name']}"] = cookie.get('value', '')
            
            # Add default Chrome headers
            headers['User-Agent'] = self.CUSTOM_HEADERS.get('Chrome', {}).get('User-Agent', '')
            headers['Accept-Language'] = 'en-US,en;q=0.9'
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['Sec-Fetch-Dest'] = 'document'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-Site'] = 'none'
            
            return headers if headers else None
        except Exception as e:
            self.log(f"Failed to extract headers from cookies: {e}")
            return None
    
    def get_http_headers(self, config):
        """Build HTTP headers based on config."""
        headers = {}
        
        auth_config = config.get('authentication', {})
        
        # Extract headers from cookie file if enabled
        if auth_config.get('use_headers_from_cookies') and auth_config.get('cookie_file_path'):
            extracted_headers = self.extract_headers_from_cookies(auth_config['cookie_file_path'])
            if extracted_headers:
                headers.update(extracted_headers)
        
        # Apply custom headers if enabled
        if auth_config.get('use_custom_headers'):
            header_type = auth_config.get('custom_header_type', 'Desktop')
            custom_header = self.CUSTOM_HEADERS.get(header_type, {})
            headers.update(custom_header)
        
        return headers if headers else None


class PlaylistSelectorWindow(ctk.CTkToplevel):
    """Popup window to select videos from a playlist."""

    def __init__(self, parent, playlist_info):
        super().__init__(parent)
        self.transient(parent)
        self.title("Playlist Video Selector")
        self.geometry("700x600")
        self.parent = parent
        self.playlist_info = playlist_info
        self.selected_videos = []
        self.checkboxes = []
        self.check_vars = []
        
        self.setup_ui()

    def setup_ui(self):
        # Header frame
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(padx=10, pady=10, fill="x")
        
        ctk.CTkLabel(header_frame, text=f"Playlist: {self.playlist_info['title']}", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text=f"Uploader: {self.playlist_info['uploader']} | Videos: {len(self.playlist_info['videos'])}", 
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 0))
        
        # Button frame for Select/Unselect All
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkButton(button_frame, text="Select All", command=self.select_all, width=100).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Unselect All", command=self.unselect_all, width=100).pack(side="left", padx=5)
        
        # Scrollable frame for videos
        scrollable_frame = ctk.CTkScrollableFrame(self)
        scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Add checkboxes for each video
        for idx, video in enumerate(self.playlist_info['videos']):
            var = ctk.BooleanVar(value=True)  # Default selected
            self.check_vars.append(var)
            
            video_frame = ctk.CTkFrame(scrollable_frame)
            video_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=5)
            video_frame.grid_columnconfigure(1, weight=1)
            
            # Checkbox
            checkbox = ctk.CTkCheckBox(video_frame, text="", variable=var)
            checkbox.grid(row=0, column=0, padx=5)
            self.checkboxes.append(checkbox)
            
            # Video info
            duration_str = time.strftime('%H:%M:%S', time.gmtime(video.get('duration', 0)))
            info_text = f"{video['title']} ({duration_str})"
            label = ctk.CTkLabel(video_frame, text=info_text, wraplength=600, justify="left")
            label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Bottom frame with actions
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(padx=10, pady=10, fill="x")
        bottom_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(bottom_frame, text="Download Selected", command=self.on_confirm).grid(row=0, column=0, padx=5)
        ctk.CTkButton(bottom_frame, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=5)

    def select_all(self):
        for var in self.check_vars:
            var.set(True)

    def unselect_all(self):
        for var in self.check_vars:
            var.set(False)

    def on_confirm(self):
        """Get selected videos and store them."""
        self.selected_videos = []
        for idx, var in enumerate(self.check_vars):
            if var.get():
                self.selected_videos.append(self.playlist_info['videos'][idx])
        
        if not self.selected_videos:
            messagebox.showwarning("No Selection", "Please select at least one video.")
            return
        
        # Set parent's playlist videos and close
        self.parent.selected_playlist_videos = self.selected_videos
        self.parent.is_playlist_mode = True
        self.destroy()


class SettingsWindow(ctk.CTkToplevel):
    """Advanced Settings Window"""

    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.title("Advanced Settings")
        self.geometry("800x600")
        self.parent = parent
        self.config_path = 'config.json'
        self.config = parent.downloader.config
        self.vars = {}
        self.tab_view = ctk.CTkTabview(self, anchor="w")
        self.tab_view.pack(expand=True, fill="both", padx=10, pady=10)
        self.create_tabs()
        save_button = ctk.CTkButton(
            self, text="Save and Close", command=self.save_and_close)
        save_button.pack(pady=10, padx=10, side="right")

    def create_tabs(self):
        tabs = {"Download": self.create_download_tab, "Output": self.create_output_tab, "Subtitles": self.create_subtitles_tab,
                "Metadata": self.create_metadata_tab, "Post-Processing": self.create_postprocessing_tab,
                "Network": self.create_network_tab, "Authentication": self.create_auth_tab,
                "Appearance": self.create_appearance_tab, "Updates": self.create_updates_tab}
        for name, func in tabs.items():
            func(self.tab_view.add(name))

    def create_download_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        self.add_entry(tab, "save_path", "Save Path",
                       "download", 0, has_browse=True)
        self.add_entry(tab, "filename_template",
                       "Filename Template", "download", 1)
        self.add_entry(tab, "retries", "Retries",
                       "download", 2, is_number=True)
        self.add_entry(tab, "fragment_retries",
                       "Fragment Retries", "download", 3, is_number=True)
        self.add_entry(tab, "concurrent_fragment_downloads",
                       "Concurrent Fragments", "download", 4, is_number=True)
        self.add_entry(tab, "limit_rate",
                       "Rate Limit (e.g., 5M, 100K)", "download", 5)

    def create_output_tab(self, tab):
        self.add_checkbox(tab, "keep_video",
                          "Keep Video after Post-processing", "output", 0)
        self.add_checkbox(tab, "writedescription",
                          "Write description to .description file", "output", 1)
        self.add_checkbox(tab, "writeinfojson",
                          "Write metadata to .info.json file", "output", 2)
        self.add_checkbox(tab, "writeannotations",
                          "Write annotations to .annotations.xml file", "output", 3)
        self.add_checkbox(tab, "writethumbnail",
                          "Write thumbnail to disk", "output", 4)

    def create_subtitles_tab(self, tab):
        self.add_checkbox(tab, "writesubtitles",
                          "Download subtitles", "subtitles", 0)
        self.add_checkbox(tab, "writeautomaticsub",
                          "Download automatic subtitles", "subtitles", 1)
        self.add_list_entry(tab, "subtitleslangs",
                            "Languages (comma-sep)", "subtitles", 2)
        self.add_entry(tab, "subtitlesformat", "Format", "subtitles", 3)

    def create_metadata_tab(self, tab):
        self.add_checkbox(tab, "embed_metadata",
                          "Embed metadata in file", "metadata", 0)
        self.add_checkbox(tab, "embed_thumbnail",
                          "Embed thumbnail", "metadata", 1)
        self.add_checkbox(tab, "embed_subtitles",
                          "Embed subtitles", "metadata", 2)

    def create_postprocessing_tab(self, tab):
        self.add_checkbox(tab, "use_sponsorblock",
                          "Use SponsorBlock", "post-processing", 0)
        self.add_list_entry(tab, "sponsorblock_mark",
                            "SponsorBlock - Mark categories", "post-processing", 1)
        self.add_list_entry(tab, "sponsorblock_remove",
                            "SponsorBlock - Remove categories", "post-processing", 2)
        self.add_checkbox(tab, "extract_audio",
                          "Extract Audio", "post-processing", 3)
        self.add_dropdown(tab, "audio_format", "Audio Format", "post-processing",
                          4, ["best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav"])
        self.add_entry(tab, "audio_quality",
                       "Audio Quality (e.g. 192K)", "post-processing", 5)

    def create_network_tab(self, tab):
        self.add_checkbox(tab, "use_proxy", "Use Proxy", "network", 0)
        self.add_entry(tab, "proxy_url", "Proxy URL", "network", 1)
        self.add_entry(tab, "socket_timeout",
                       "Socket Timeout (seconds)", "network", 2, is_number=True)
        self.add_entry(tab, "source_address",
                       "Source IP Address", "network", 3)

    def create_auth_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        
        self.add_checkbox(tab, "use_cookies",
                          "Use Cookies from Browser", "authentication", 0)
        self.add_dropdown(tab, "cookie_browser", "Cookie Browser", "authentication", 1, [
                          "chrome", "firefox", "edge", "opera", "vivaldi", "safari"])
        ctk.CTkButton(tab, text="Open Browser to Login", command=self.open_browser_and_enable_cookies).grid(
            row=1, column=2, padx=10, pady=10, sticky="w")
        
        # Cookie file loader
        self.add_entry(tab, "cookie_file_path", "Cookie File Path (JSON)", "authentication", 2, has_browse=True)
        ctk.CTkButton(tab, text="Load Cookie File", command=self.load_cookie_file).grid(
            row=2, column=2, padx=10, pady=10, sticky="w")
        
        # Custom headers section
        self.add_checkbox(tab, "use_custom_headers", "Use Custom Headers", "authentication", 3)
        self.add_dropdown(tab, "custom_header_type", "Header Type", "authentication", 4, [
            "Desktop", "Android", "iOS", "TV", "Chrome", "Firefox", "Safari", "Edge", "Samsung Smart TV", "Roku"
        ])
        
        # Use headers from cookies
        self.add_checkbox(tab, "use_headers_from_cookies", "Extract Headers from Cookie File", "authentication", 5)

    def load_cookie_file(self):
        """Load and validate cookie file."""
        try:
            cookie_path_var, _, _, _ = self.vars.get('cookie_file_path')
            if not cookie_path_var:
                messagebox.showerror("Error", "Could not find cookie path field.")
                return
            
            cookie_path = cookie_path_var.get()
            if not cookie_path or not Path(cookie_path).exists():
                messagebox.showerror("Error", "Cookie file path is invalid or does not exist.")
                return
            
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if isinstance(cookies, list) and len(cookies) > 0:
                messagebox.showinfo("Success", f"Loaded {len(cookies)} cookies from file.")
            else:
                messagebox.showwarning("Warning", "Cookie file is empty or invalid format.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Cookie file is not valid JSON.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cookie file: {e}")
    
    def open_browser_and_enable_cookies(self):
        # Keep the browser selection for yt-dlp, but don't use it for opening the URL here.
        browser_var, _, _, _ = self.vars.get('cookie_browser')
        if not browser_var:
            messagebox.showerror("Error", "Could not find browser selection dropdown.")
            return
        
        selected_browser_for_cookies = browser_var.get()

        use_cookies_var, _, _, _ = self.vars.get('use_cookies')
        if use_cookies_var:
            use_cookies_var.set(True)
        else:
            messagebox.showwarning("Warning", "Could not find 'Use Cookies' checkbox to enable it.")

        try:
            messagebox.showinfo(
                "Opening Browser", 
                f"Attempting to open YouTube in your default browser for login.\n\n"
                f"Please ensure the browser selected in the dropdown ('{selected_browser_for_cookies.capitalize()}') is the one you log in with.\n\n"
                f"After logging in, close the tab and save settings."
            )
            # This opens the URL in the user's default browser.
            webbrowser.open("https://www.youtube.com", new=1, autoraise=True)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while opening the browser: {e}")

    def create_appearance_tab(self, tab):
        self.add_dropdown(tab, "theme", "Theme", "app", 0, [
                          "System", "Dark", "Light"], command=self.change_theme)

    def create_updates_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.update_log = ctk.CTkTextbox(tab, height=300)
        self.update_log.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Button frame for update buttons
        button_frame = ctk.CTkFrame(tab)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(button_frame, text="Check and Update", command=self.run_updates).grid(
            row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Force Update (Reinstall) All Modules", command=self.run_force_updates, 
                     fg_color="red").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def add_checkbox(self, tab, name, text, section, row): self._add_widget(
        tab, name, text, section, row, "checkbox")

    def add_entry(self, tab, name, text, section, row, is_number=False, is_list=False, has_browse=False): self._add_widget(
        tab, name, text, section, row, "entry", is_number=is_number, is_list=is_list, has_browse=has_browse)

    def add_dropdown(self, tab, name, text, section, row, values, command=None): self._add_widget(
        tab, name, text, section, row, "dropdown", values=values, command=command)

    def add_list_entry(self, tab, name, text, section, row): self.add_entry(
        tab, name, text, section, row, is_list=True)

    def _add_widget(self, tab, name, text, section_name, row, w_type, **kwargs):
        section = self.config[section_name]
        ctk.CTkLabel(tab, text=text).grid(
            row=row, column=0, padx=10, pady=10, sticky="w")
        current_value = section.get(name)
        if kwargs.get("is_list"):
            current_value = ", ".join(current_value) if isinstance(
                current_value, list) else ""

        if w_type == "checkbox":
            var = ctk.BooleanVar(value=current_value)
            ctk.CTkCheckBox(tab, text="", variable=var).grid(
                row=row, column=1, padx=10, pady=10, sticky="w")
        elif w_type == "entry":
            var = ctk.StringVar(value=current_value)
            entry_widget = ctk.CTkEntry(tab, textvariable=var)
            entry_widget.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
            EntryContextMenu(entry_widget)  # Add context menu to all entries
            if kwargs.get("has_browse"):
                ctk.CTkButton(tab, text="Browse...", width=80, command=lambda: self.browse_path(
                    var)).grid(row=row, column=2, padx=(0, 10))
        elif w_type == "dropdown":
            var = ctk.StringVar(value=str(current_value).capitalize(
            ) if name == "theme" else str(current_value))
            ctk.CTkOptionMenu(tab, variable=var, values=kwargs.get("values"), command=kwargs.get(
                "command")).grid(row=row, column=1, padx=10, pady=10, sticky="w")

        self.vars[name] = (var, section_name, kwargs.get(
            "is_number", False), kwargs.get("is_list", False))

    def browse_path(self, path_var):
        if (directory := filedialog.askdirectory()):
            path_var.set(directory)

    def change_theme(self, new_theme: str): ctk.set_appearance_mode(
        new_theme.lower())

    def run_updates(self): 
        threading.Thread(target=self._update_dependencies, daemon=True).start()
    
    def run_force_updates(self): 
        threading.Thread(target=self._force_update_dependencies, daemon=True).start()

    def _update_dependencies(self):
        if not self.update_log.winfo_exists():
            return
        self.update_log.delete("1.0", "end")
        self.update_log.insert("end", "Starting update check...\n")
        try:
            command = [sys.executable, '-m', 'pip', 'install',
                       '--upgrade', 'yt-dlp', 'customtkinter', 'Pillow', 'requests']
            if self.update_log.winfo_exists():
                self.update_log.insert(
                    "end", f"Running: {' '.join(command)}\n\n")
            else:
                return
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            for line in iter(process.stdout.readline, ''):
                if not self.update_log.winfo_exists():
                    process.kill()
                    break
                self.update_log.insert("end", line)
                self.update_log.see("end")
            process.stdout.close()
            return_code = process.wait()
            if self.update_log.winfo_exists():
                self.update_log.insert(
                    "end", f"\n\nUpdate check finished with code: {return_code}.")
        except Exception as e:
            if self.update_log.winfo_exists():
                self.update_log.insert("end", f"\n\nAn error occurred: {e}")
    
    def _force_update_dependencies(self):
        if not self.update_log.winfo_exists():
            return
        self.update_log.delete("1.0", "end")
        self.update_log.insert("end", "Starting FORCE update (reinstall)...\n")
        try:
            command = [sys.executable, '-m', 'pip', 'install', '--force-reinstall',
                       '--no-cache-dir', 'yt-dlp', 'customtkinter', 'Pillow', 'requests']
            if self.update_log.winfo_exists():
                self.update_log.insert(
                    "end", f"Running: {' '.join(command)}\n\n")
            else:
                return
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            for line in iter(process.stdout.readline, ''):
                if not self.update_log.winfo_exists():
                    process.kill()
                    break
                self.update_log.insert("end", line)
                self.update_log.see("end")
            process.stdout.close()
            return_code = process.wait()
            if self.update_log.winfo_exists():
                self.update_log.insert(
                    "end", f"\n\nForce update finished with code: {return_code}.")
        except Exception as e:
            if self.update_log.winfo_exists():
                self.update_log.insert("end", f"\n\nAn error occurred: {e}")

    def save_and_close(self):
        for name, (var, section_name, is_number, is_list) in self.vars.items():
            value = var.get()
            if isinstance(var, ctk.BooleanVar):
                value = bool(value)
            if is_number:
                value = int(value) if str(value).isdigit() else 0
            if is_list:
                value = [item.strip()
                         for item in value.split(',') if item.strip()]
            if name == 'theme':
                value = value.lower()
            self.config[section_name][name] = value
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        self.parent.downloader.config = self.config
        messagebox.showinfo(
            "Settings Saved", "Settings have been saved successfully.")
        self.destroy()


class MainWindow(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.downloader = YouTubeDownloader(
            log_callback=self.log_to_gui,
            progress_callback=self.update_progress_display,
            postprocessor_callback=self.update_postprocessor_display
        )
        ctk.set_appearance_mode(
            self.downloader.config["app"].get("theme", "dark"))
        self.title("YouTube Professional Downloader")
        self.geometry("1200x800")
        ctk.set_default_color_theme("blue")
        self.video_info = None
        self.settings_window = None
        self.quality_map = {}
        self.video_formats = []
        self.audio_formats = []
        self.container_formats = []
        self.is_playlist_mode = False
        self.selected_playlist_videos = []
        self.current_url = None
        # Queue management
        self.download_queue = []  # List of dicts with video info and quality settings
        # Download control
        self.is_downloading = False
        self.cancel_download = False
        self.skip_current_video = False
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        url_frame = ctk.CTkFrame(self)
        url_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(
            url_frame, placeholder_text="Enter YouTube URL...")
        self.url_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        EntryContextMenu(self.url_entry)  # Add right-click context menu
        ctk.CTkButton(url_frame, text="Fetch Info", command=self.fetch_video_info).grid(
            row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(url_frame, text="Settings", command=self.open_settings).grid(
            row=0, column=2, padx=(0, 10), pady=10)
        
        # Side-by-side frame for Queue and Video Information
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Queue display frame (LEFT)
        queue_frame = ctk.CTkFrame(content_frame)
        queue_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        queue_frame.grid_columnconfigure(0, weight=1)
        queue_frame.grid_rowconfigure(1, weight=1)
        
        queue_label = ctk.CTkLabel(queue_frame, text="Download Queue", font=ctk.CTkFont(size=12, weight="bold"))
        queue_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.queue_display = ctk.CTkTextbox(queue_frame, state="disabled")
        self.queue_display.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Queue buttons frame
        queue_button_frame = ctk.CTkFrame(queue_frame)
        queue_button_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkButton(queue_button_frame, text="Add to Queue", command=self.add_to_queue, width=100).pack(side="left", padx=5)
        ctk.CTkButton(queue_button_frame, text="Clear Queue", command=self.clear_queue, width=100).pack(side="left", padx=5)
        
        # Video Information frame (RIGHT)
        info_outer_frame = ctk.CTkFrame(content_frame)
        info_outer_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        info_outer_frame.grid_columnconfigure(0, weight=1)
        info_outer_frame.grid_rowconfigure(0, weight=1)
        
        self.info_frame = ctk.CTkScrollableFrame(
            info_outer_frame, label_text="Video Information")
        self.info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.thumbnail_label = ctk.CTkLabel(self.info_frame, text="")
        self.thumbnail_label.grid(row=0, column=0, pady=10)
        self.title_label = ctk.CTkLabel(self.info_frame, text="Enter a URL and click 'Fetch Info'", font=ctk.CTkFont(
            size=16, weight="bold"), wraplength=700)
        self.title_label.grid(row=1, column=0, pady=(0, 10))
        self.details_label = ctk.CTkLabel(
            self.info_frame, text="", font=ctk.CTkFont(size=12))
        self.details_label.grid(row=2, column=0, pady=(0, 10))
        options_frame = ctk.CTkFrame(self)
        options_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        options_frame.grid_columnconfigure((1, 3, 5), weight=1)  # Flexible columns for dropdowns
        self.quality_var = ctk.StringVar(value="1080p")
        ctk.CTkLabel(options_frame, text="Quality:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w")
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame, variable=self.quality_var, values=["1080p"], command=self.on_quality_change)
        self.quality_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.format_var = ctk.StringVar(value="mp4")
        ctk.CTkLabel(options_frame, text="Format:").grid(
            row=0, column=2, padx=10, pady=5, sticky="w")
        self.format_menu = ctk.CTkOptionMenu(
            options_frame, variable=self.format_var, values=["mp4"])
        self.format_menu.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.audio_var = ctk.StringVar(value="best")
        ctk.CTkLabel(options_frame, text="Audio:").grid(
            row=0, column=4, padx=10, pady=5, sticky="w")
        self.audio_menu = ctk.CTkOptionMenu(
            options_frame, variable=self.audio_var, values=["best"])
        self.audio_menu.grid(row=0, column=5, padx=10, pady=5, sticky="ew")
        
        # Action buttons for single videos
        self.add_queue_button = ctk.CTkButton(options_frame, text="Add to Queue", command=self.add_to_queue, width=120)
        self.add_queue_button.grid(row=0, column=6, padx=(20, 10), pady=5)
        self.open_browser_button = ctk.CTkButton(options_frame, text="Open in Browser", command=self._open_in_browser, width=120)
        self.open_browser_button.grid(row=0, column=7, padx=(0, 10), pady=5)
        
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        progress_frame.grid_columnconfigure(1, weight=1)
        
        # Overall progress for single video or playlist overall
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="w")
        
        # Cancel button for overall progress
        self.cancel_button = ctk.CTkButton(progress_frame, text="Cancel", command=self.cancel_current_download, 
                                          state="disabled", fg_color="red", width=80, height=25)
        self.cancel_button.grid(row=1, column=0, padx=(10, 5), pady=(0, 5), sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=1, columnspan=1, padx=5, pady=(0, 5), sticky="ew")
        
        # Per-video progress (for playlists, hidden for single videos)
        self.per_video_label = ctk.CTkLabel(progress_frame, text="")
        self.per_video_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="w")
        
        # Skip button for single video
        self.skip_button = ctk.CTkButton(progress_frame, text="Skip", command=self.skip_video, 
                                        state="disabled", fg_color="orange", width=80, height=25)
        self.skip_button.grid(row=3, column=0, padx=(10, 5), pady=(0, 10), sticky="w")
        
        self.per_video_progress_bar = ctk.CTkProgressBar(progress_frame)
        self.per_video_progress_bar.set(0)
        self.per_video_progress_bar.grid(row=3, column=1, columnspan=1, padx=5, pady=(0, 10), sticky="ew")
        
        ctk.CTkButton(self, text="Download", command=self.start_download, height=40, font=ctk.CTkFont(
            size=14, weight="bold")).grid(row=4, column=0, padx=10, pady=10, sticky="ew")

    def fetch_video_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return messagebox.showerror("Error", "Please enter a URL")
        self.title_label.configure(text="Fetching video information...")
        self.details_label.configure(text="")
        self.thumbnail_label.configure(image=None)
        threading.Thread(target=self._fetch_info_thread,
                         args=(url,), daemon=True).start()

    def _fetch_info_thread(self, url):
        try:
            self.current_url = url
            # First try to detect if it's a playlist
            try:
                playlist_info = self.downloader.get_playlist_info(url)
                if playlist_info.get('videos') and len(playlist_info['videos']) > 1:
                    # It's a playlist with multiple videos
                    self.after(0, self.show_playlist_selector, playlist_info)
                    return
            except Exception:
                # Not a playlist or error - continue with single video
                pass
            
            # It's a single video
            self.video_info = self.downloader.get_video_info(url)
            self.is_playlist_mode = False
            self.after(0, self.update_video_info, self.video_info)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", f"Failed to fetch info: {e}"))
            self.after(0, lambda: self.title_label.configure(
                text="Failed to fetch info. Please try again."))

    def update_video_info(self, info):
        self.title_label.configure(text=info['title'])
        self.details_label.configure(
            text=f"Uploader: {info.get('uploader', 'N/A')} | Duration: {time.strftime('%H:%M:%S', time.gmtime(info.get('duration', 0)))}")
        
        # Clear and rebuild info frame with all available info
        for widget in self.info_frame.winfo_children():
            if widget != self.thumbnail_label and widget != self.title_label and widget != self.details_label:
                widget.destroy()
        
        # Add extended info sections below details
        row = 3
        
        # Stats section
        views = info.get('views')
        likes = info.get('likes')
        if views or likes:
            stats_text = ""
            if views:
                stats_text += f"Views: {views:,}"
            if likes:
                stats_text += f" | Likes: {likes:,}"
            if stats_text:
                ctk.CTkLabel(self.info_frame, text=stats_text, font=ctk.CTkFont(size=10)).grid(
                    row=row, column=0, pady=5, sticky="w")
                row += 1
        
        # Upload date
        upload_date = info.get('upload_date')
        if upload_date:
            try:
                formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                ctk.CTkLabel(self.info_frame, text=f"Uploaded: {formatted_date}", font=ctk.CTkFont(size=10)).grid(
                    row=row, column=0, pady=5, sticky="w")
                row += 1
            except:
                pass
        
        # Subtitles
        subtitles = info.get('subtitles', [])
        if subtitles:
            sub_text = f"Subtitles: {', '.join(subtitles[:5])}"
            if len(subtitles) > 5:
                sub_text += f" +{len(subtitles)-5} more"
            ctk.CTkLabel(self.info_frame, text=sub_text, font=ctk.CTkFont(size=10)).grid(
                row=row, column=0, pady=5, sticky="w")
            row += 1
        
        # Tags
        tags = info.get('tags', [])
        if tags:
            tags_text = f"Tags: {', '.join(tags[:5])}"
            if len(tags) > 5:
                tags_text += f" +{len(tags)-5} more"
            ctk.CTkLabel(self.info_frame, text=tags_text, font=ctk.CTkFont(size=10)).grid(
                row=row, column=0, pady=5, sticky="w")
            row += 1
        
        # Description
        description = info.get('description')
        if description:
            desc_label = ctk.CTkLabel(self.info_frame, text="Description:", font=ctk.CTkFont(size=11, weight="bold"))
            desc_label.grid(row=row, column=0, pady=(10, 5), sticky="w")
            row += 1
            
            desc_text = ctk.CTkTextbox(self.info_frame, height=100, state="disabled")
            desc_text.grid(row=row, column=0, pady=(0, 10), sticky="ew")
            desc_text.configure(state="normal")
            desc_text.insert("1.0", description[:500] + ("..." if len(description) > 500 else ""))
            desc_text.configure(state="disabled")
            row += 1
        
        unique_formats = {}
        self.quality_map = {}
        # Store video formats for later use
        self.video_formats = info['formats'].get('video', [])
        self.audio_formats = info['formats'].get('audio', [])
        self.container_formats = info['formats'].get('formats', ['mp4'])
        
        sorted_formats = sorted(self.video_formats, key=lambda f: (int(f.get(
            'resolution', '0x0').split('x')[1]), int(f.get('fps', 0) or 0)), reverse=True)
        for f in sorted_formats:
            res = f.get('resolution')
            height = res.split('x')[1]
            if not res:
                continue
            display_key = f"{height}p"
            if (fps := f.get('fps')) and fps > 30:
                display_key += str(fps)
            if (note := f.get('format_note')) and note and "hdr" in note.lower():
                display_key += " (HDR)"
            if display_key not in unique_formats:
                unique_formats[display_key] = height
        self.quality_map = unique_formats
        self.quality_map["Audio Only"] = "audio"
        self.quality_menu.configure(values=list(self.quality_map.keys()), command=self.on_quality_change)
        default_quality = next((q for q in ["1080p", "720p"] if q in self.quality_map), list(
            self.quality_map.keys())[0])
        self.quality_var.set(default_quality)
        # Build audio format options
        audio_options = ["best"]
        if self.audio_formats:
            seen_codecs = set()
            for audio in sorted(self.audio_formats, key=lambda a: a.get('abr') or 0, reverse=True):
                codec = audio.get('acodec', 'unknown')
                if codec not in seen_codecs:
                    audio_options.append(codec)
                    seen_codecs.add(codec)
        self.audio_menu.configure(values=audio_options)
        self.audio_var.set("best")
        # Set initial format options based on current quality
        self.on_quality_change(default_quality)
        if info['thumbnail']:
            threading.Thread(target=self._load_thumbnail, args=(
                info['thumbnail'],), daemon=True).start()

    def on_quality_change(self, selected_quality):
        """Update format options based on selected quality - called when quality selection changes."""
        if selected_quality == "Audio Only":
            # For audio, show audio format options
            audio_formats = ["best", "mp3", "aac", "opus", "wav", "flac"]
            
            # Add codecs from actual audio tracks if available
            if self.audio_formats:
                seen_codecs = set()
                for audio in sorted(self.audio_formats, key=lambda a: a.get('abr') or 0, reverse=True):
                    codec = audio.get('acodec', 'unknown')
                    abr = audio.get('abr', 0)
                    # Create display string with bitrate if available
                    if codec not in seen_codecs and codec != 'opus' and codec not in ['best', 'mp3', 'aac', 'opus', 'wav', 'flac']:
                        if abr:
                            display = f"{codec} ({abr}kbps)"
                        else:
                            display = codec
                        audio_formats.append(display)
                        seen_codecs.add(codec)
            
            self.format_menu.configure(values=audio_formats)
            # Set default to 'best' for audio
            self.format_var.set("best" if "best" in audio_formats else audio_formats[0])
            
        else:
            # For video, show all available video format variants for the selected quality
            selected_height = self.quality_map.get(selected_quality)
            video_format_options = []
            
            if selected_height and selected_height != "audio":
                # Find all formats matching the selected quality
                seen_codecs = {}  # Track by codec to avoid duplicates
                
                for fmt in self.video_formats:
                    res = fmt.get('resolution', '')
                    if not res:
                        continue
                    height = res.split('x')[1] if 'x' in res else '0'
                    
                    # Match the selected quality height
                    if height == selected_height:
                        codec = fmt.get('vcodec', 'unknown')
                        fps = fmt.get('fps', 0)
                        filesize = fmt.get('filesize', 0)
                        
                        # Create a descriptive display string
                        size_str = f"{filesize / (1024*1024):.1f}MB" if filesize else "unknown size"
                        
                        if fps and fps > 30:
                            display = f"{codec} @ {int(fps)}fps ({size_str})"
                        else:
                            display = f"{codec} ({size_str})"
                        
                        # Only add if we haven't seen this exact codec yet
                        if codec not in seen_codecs:
                            video_format_options.append(display)
                            seen_codecs[codec] = True
            
            # If no specific formats found, use container formats as fallback
            if not video_format_options:
                video_format_options = self.container_formats if self.container_formats else ['mp4', 'mkv', 'webm']
            
            self.format_menu.configure(values=video_format_options)
            self.format_var.set(video_format_options[0] if video_format_options else 'mp4')

    def _load_thumbnail(self, url):
        if Image is None:
            self.log_to_gui("PIL/Pillow not available. Skipping thumbnail.")
            return
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            max_width = 700
            w_percent = (max_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(
                light_image=img, dark_image=img, size=img.size)
            self.after(0, self.thumbnail_label.configure,
                       {"image": photo, "text": ""})
        except Exception as e:
            self.log_to_gui(f"Failed to load thumbnail: {e}")

    def show_playlist_selector(self, playlist_info):
        """Display the playlist selector window."""
        playlist_window = PlaylistSelectorWindow(self, playlist_info)
        playlist_window.focus()
        # Wait for window to close and check if videos were selected
        self.wait_window(playlist_window)
        if self.is_playlist_mode and self.selected_playlist_videos:
            self.title_label.configure(text=f"Playlist: {playlist_info['title']}")
            self.details_label.configure(
                text=f"Selected {len(self.selected_playlist_videos)} video(s) from {len(playlist_info['videos'])} total")
            # Enable quality selection menus for playlist
            self._setup_playlist_quality_options()
            # Auto-add selected videos to queue
            self._auto_add_playlist_to_queue()

    def _setup_playlist_quality_options(self):
        """Setup quality/format/audio options for playlist downloads with default values."""
        # For playlists, use standard quality options since we don't have individual video info
        quality_options = ["1080p", "720p", "480p", "360p", "240p", "Audio Only"]
        self.quality_menu.configure(values=quality_options, command=lambda q: self._on_playlist_quality_change(q))
        self.quality_var.set("720p")
        
        # Set format options for video quality
        format_options = ["mp4", "mkv", "webm"]
        self.format_menu.configure(values=format_options, command=lambda f: self._on_playlist_options_change())
        self.format_var.set("mp4")
        
        # Set audio options
        audio_options = ["best", "aac", "mp3", "opus"]
        self.audio_menu.configure(values=audio_options, command=lambda a: self._on_playlist_options_change())
        self.audio_var.set("best")

    def _auto_add_playlist_to_queue(self):
        """Automatically add selected playlist videos to queue."""
        if not self.is_playlist_mode or not self.selected_playlist_videos:
            return
        
        # Clear existing queue items for playlist
        self.download_queue.clear()
        
        quality = self.quality_var.get()
        format_choice = self.format_var.get()
        audio = self.audio_var.get()
        
        for video in self.selected_playlist_videos:
            queue_item = {
                'title': video['title'],
                'url': video['url'],
                'quality': quality,
                'format': format_choice,
                'audio': audio,
                'duration': video.get('duration', 0)
            }
            self.download_queue.append(queue_item)
        
        self.update_queue_display()
    
    def _on_playlist_quality_change(self, selected_quality=None):
        """Handle quality change in playlist mode - update formats and queue."""
        if not self.is_playlist_mode:
            return
        
        if selected_quality is None:
            selected_quality = self.quality_var.get()
        
        # Update format menu based on quality
        if selected_quality == "Audio Only":
            format_options = ["best", "mp3", "aac", "opus", "wav"]
            self.format_menu.configure(values=format_options)
            # Only update if current value is not in new options
            current_format = self.format_var.get()
            if current_format not in format_options:
                self.format_var.set("best")
        else:
            format_options = ["mp4", "mkv", "webm", "avi", "flv"]
            self.format_menu.configure(values=format_options)
            # Only update if current value is not in new options
            current_format = self.format_var.get()
            if current_format not in format_options:
                self.format_var.set("mp4")
        
        # Update queue items with new quality
        self._update_queue_quality()
    
    def _on_playlist_options_change(self):
        """Handle format/audio change in playlist mode - update queue."""
        if not self.is_playlist_mode:
            return
        
        self._update_queue_quality()
    
    def _update_queue_quality(self):
        """Update all queue items with current quality/format/audio settings."""
        if not self.is_playlist_mode or not self.download_queue:
            return
        
        quality = self.quality_var.get()
        format_choice = self.format_var.get()
        audio = self.audio_var.get()
        
        # Update all items in queue with new settings
        for item in self.download_queue:
            item['quality'] = quality
            item['format'] = format_choice
            item['audio'] = audio
        
        self.update_queue_display()

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        self.settings_window.focus()

    def _open_in_browser(self):
        """Open the current video URL in the default browser."""
        url = self.url_entry.get().strip()
        if url:
            webbrowser.open(url)

    def add_to_queue(self):
        """Add current video or playlist videos to the download queue."""
        if self.is_playlist_mode:
            # Add all selected playlist videos with current quality settings
            if not self.selected_playlist_videos:
                messagebox.showerror("Error", "No playlist videos selected.")
                return
            
            quality = self.quality_var.get()
            format_choice = self.format_var.get()
            audio = self.audio_var.get()
            
            for video in self.selected_playlist_videos:
                queue_item = {
                    'title': video['title'],
                    'url': video['url'],
                    'quality': quality,
                    'format': format_choice,
                    'audio': audio,
                    'duration': video.get('duration', 0)
                }
                self.download_queue.append(queue_item)
            
            messagebox.showinfo("Success", f"Added {len(self.selected_playlist_videos)} video(s) to queue.")
        else:
            # Add single video with current quality settings
            if not self.video_info:
                messagebox.showerror("Error", "Please fetch video info first.")
                return
            
            quality = self.quality_var.get()
            format_choice = self.format_var.get()
            audio = self.audio_var.get()
            
            queue_item = {
                'title': self.video_info.get('title', 'Unknown'),
                'url': self.url_entry.get().strip(),
                'quality': quality,
                'format': format_choice,
                'audio': audio,
                'duration': self.video_info.get('duration', 0)
            }
            self.download_queue.append(queue_item)
            messagebox.showinfo("Success", "Video added to queue.")
        
        self.update_queue_display()

    def clear_queue(self):
        """Clear all items from the download queue."""
        if not self.download_queue:
            messagebox.showwarning("Queue Empty", "Queue is already empty.")
            return
        
        self.download_queue.clear()
        self.update_queue_display()
        messagebox.showinfo("Queue Cleared", "All items removed from queue.")

    def update_queue_display(self):
        """Update the queue display textbox with current queue items."""
        self.queue_display.configure(state="normal")
        self.queue_display.delete("1.0", "end")
        
        if not self.download_queue:
            self.queue_display.insert("end", "Queue is empty")
        else:
            for idx, item in enumerate(self.download_queue, 1):
                duration_str = time.strftime('%H:%M:%S', time.gmtime(item.get('duration', 0)))
                text = f"{idx}. {item['title'][:50]}\n"
                text += f"   Quality: {item['quality']} | Format: {item['format']} | Audio: {item['audio']}\n"
                text += f"   Duration: {duration_str}\n\n"
                self.queue_display.insert("end", text)
        
        self.queue_display.configure(state="disabled")

    def cancel_current_download(self):
        """Cancel the current download process."""
        if self.is_downloading:
            self.cancel_download = True
            self.cancel_button.configure(state="disabled")
            self.skip_button.configure(state="disabled")
            self.progress_label.configure(text="Cancelling download...")
    
    def skip_video(self):
        """Skip the current video and move to the next."""
        if self.is_downloading:
            self.skip_current_video = True
            self.skip_button.configure(state="disabled")
            self.per_video_label.configure(text="Skipping video...")
    
    def start_download(self):
        """Start downloading all items in the queue."""
        if not self.download_queue:
            return messagebox.showerror("Error", "Queue is empty. Please add items to queue first.")
        
        self.cancel_download = False
        self.skip_current_video = False
        self.is_downloading = True
        self.cancel_button.configure(state="normal")
        self.skip_button.configure(state="normal")
        
        self.progress_bar.set(0)
        self.per_video_progress_bar.set(0)
        self.progress_label.configure(text="Starting queue download...")
        self.per_video_label.configure(text="")
        threading.Thread(target=self.download_from_queue, daemon=True).start()

    def download_from_queue(self):
        """Download all items from the queue with their respective quality settings."""
        total_items = len(self.download_queue)
        
        for idx, queue_item in enumerate(self.download_queue):
            if self.cancel_download:
                self.after(0, lambda: (
                    self.progress_label.configure(text="Download cancelled by user"),
                    self.cancel_button.configure(state="disabled"),
                    self.skip_button.configure(state="disabled")
                ))
                break
            
            # Update overall queue progress
            queue_progress = idx / total_items
            self.after(0, lambda q=queue_progress: self.progress_bar.set(q))
            
            # Temporarily set quality/format/audio vars for this item
            self.quality_var.set(queue_item['quality'])
            self.format_var.set(queue_item['format'])
            self.audio_var.set(queue_item['audio'])
            
            self.skip_current_video = False
            self.after(0, lambda i=idx, t=total_items, title=queue_item['title']: 
                      self.progress_label.configure(text=f"Downloading ({i+1}/{t}): {title[:50]}..."))
            self.after(0, lambda: self.per_video_label.configure(text=""))
            self.after(0, lambda: self.per_video_progress_bar.set(0))
            self.after(0, lambda: self.skip_button.configure(state="normal"))
            
            # Build options with current queue item settings
            options = self._build_download_options()
            result = self.downloader.download(queue_item['url'], options)
            
            if self.skip_current_video:
                self.after(0, lambda i=idx, t=total_items: 
                          self.progress_label.configure(text=f"Skipped. Continuing ({i+2}/{t})..."))
                self.skip_current_video = False
                continue
            
            if result['status'] == 'error':
                self.after(0, lambda title=queue_item['title'], err=result['message']: 
                          messagebox.showerror("Download Error", f"Failed to download {title}: {err}"))
        
        self.is_downloading = False
        self.after(0, lambda: (
            self.progress_label.configure(text="Queue download completed!"),
            messagebox.showinfo("Success", f"Downloaded {total_items} item(s) from queue!"),
            self.progress_bar.set(0),
            self.per_video_progress_bar.set(0),
            self.per_video_label.configure(text=""),
            self.cancel_button.configure(state="disabled"),
            self.skip_button.configure(state="disabled"),
            self.clear_queue()
        ))

    def download_playlist(self):
        """Download all selected videos from the playlist."""
        for idx, video in enumerate(self.selected_playlist_videos):
            self.after(0, lambda v=video, i=idx: self.progress_label.configure(
                text=f"Downloading {i+1}/{len(self.selected_playlist_videos)}: {v['title'][:40]}..."))
            
            options = self._build_download_options()
            result = self.downloader.download(video['url'], options)
            
            if result['status'] == 'error':
                self.after(0, lambda v=video, err=result['message']: messagebox.showerror(
                    "Download Error", f"Failed to download {v['title']}: {err}"))
        
        self.after(0, lambda: (
            self.progress_label.configure(text="Playlist download completed!"),
            messagebox.showinfo("Success", f"Downloaded {len(self.selected_playlist_videos)} video(s)"),
            self.progress_bar.set(0)
        ))

    def _build_download_options(self):
        config = self.downloader.config
        # For playlist mode, quality_map might not be populated, so we handle it differently
        if self.is_playlist_mode:
            # Map standard quality names to height values
            quality_name = self.quality_var.get()
            quality_map_playlist = {
                "1080p": "1080",
                "720p": "720",
                "480p": "480",
                "360p": "360",
                "240p": "240",
                "Audio Only": "audio"
            }
            height = quality_map_playlist.get(quality_name, "720")
        else:
            height = self.quality_map.get(self.quality_var.get())
        
        quality_is_audio = (height == "audio")
        save_path = Path(config['download']['save_path']).expanduser()
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Get custom headers if configured
        http_headers = self.downloader.get_http_headers(config)
        
        # Build the full yt-dlp options dictionary from the config
        options = {
            'verbose': True,
            'outtmpl': str(save_path / config['download']['filename_template']),
            'retries': config['download']['retries'], 'fragment_retries': config['download']['fragment_retries'],
            'concurrent_fragment_downloads': config['download']['concurrent_fragment_downloads'],
            'ratelimit': config['download']['limit_rate'] if config['download']['limit_rate'] != "0" else None,
            'writesubtitles': config['subtitles']['writesubtitles'], 'writeautomaticsub': config['subtitles']['writeautomaticsub'],
            'subtitleslangs': config['subtitles']['subtitleslangs'], 'subtitlesformat': config['subtitles']['subtitlesformat'],
            'writedescription': config['output']['writedescription'], 'writeinfojson': config['output']['writeinfojson'],
            'writeannotations': config['output']['writeannotations'], 'writethumbnail': config['output']['writethumbnail'],
            'keepvideo': config['output']['keep_video'],
            'addmetadata': config['metadata']['embed_metadata'],
            'parse_metadata': config['metadata']['parse_metadata'] if config['metadata']['parse_metadata'] else None,
            'proxy': config['network']['proxy_url'] if config['network']['use_proxy'] else None,
            'socket_timeout': config['network']['socket_timeout'],
            'source_address': config['network']['source_address'] if config['network']['source_address'] != "0.0.0.0" else None,
            'cookiesfrombrowser': (config['authentication']['cookie_browser'],) if config['authentication']['use_cookies'] else None,
            'http_headers': http_headers if http_headers else {},
            # To stabilize extraction
            'extractor_args': {'youtube': {'player_client': ['default']}},
        }
        # Handle Post Processors
        postprocessors = []
        # Get selected audio format
        selected_audio = self.audio_var.get()
        selected_format = self.format_var.get()
        
        # FFmpegExtractAudio must be first if used
        if quality_is_audio or config['post-processing']['extract_audio']:
            options[
                'format'] = 'bestaudio/best' if quality_is_audio else f'bestvideo[height<={height}]+bestaudio/best'
            # Determine audio codec
            if selected_format == "best":
                audio_codec = config['post-processing']['audio_format']
            elif selected_format == "mp3":
                audio_codec = "mp3"
            else:
                audio_codec = selected_format
            postprocessors.append(
                {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_codec, 'preferredquality': config['post-processing']['audio_quality']})
        else:  # Video or Video+Audio
            options['format'] = f'bestvideo[height<={height}]+bestaudio/best'
            # Add FFmpeg remuxing for format conversion (only for video)
            if selected_format and selected_format not in ['mp4', 'mkv', 'webm']:
                postprocessors.append({'key': 'FFmpegVideoRemuxer', 'preferedformat': selected_format})
            else:
                options['merge_output_format'] = selected_format
        if config['metadata']['embed_thumbnail']:
            postprocessors.append(
                {'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
        if config['metadata']['embed_subtitles']:
            postprocessors.append({'key': 'FFmpegEmbedSubtitle'})
        if config['post-processing']['use_sponsorblock']:
            postprocessors.append(
                {'key': 'SponsorBlock', 'categories': config['post-processing']['sponsorblock_remove']})
            postprocessors.append(
                {'key': 'ModifyChapters', 'remove_sponsor_segments': config['post-processing']['sponsorblock_mark']})

        options['postprocessors'] = postprocessors
        self.downloader.log(f"DEBUG: Using options: {options}")
        return options

    def format_bytes(self, bytes_val):
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}TB"
    
    def format_time(self, seconds):
        """Format seconds to HH:MM:SS."""
        if not seconds:
            return "N/A"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def update_progress_display(self, d):
        def _update_gui():
            if d['status'] == 'downloading':
                try:
                    total_bytes = float(d.get('total_bytes') or d.get(
                        'total_bytes_estimate', 0))
                    if total_bytes > 0:
                        downloaded_bytes = float(d.get('downloaded_bytes', 0))
                        percent = downloaded_bytes / total_bytes
                        
                        # Update per-video progress bar
                        self.per_video_progress_bar.set(percent)
                        
                        speed = d.get('speed')
                        speed_mbps = (float(speed) / (1024 * 1024)
                                      ) if speed is not None else 0
                        
                        # Format like terminal output
                        total_formatted = self.format_bytes(total_bytes)
                        downloaded_formatted = self.format_bytes(downloaded_bytes)
                        eta_str = self.format_time(d.get('eta', 0))
                        
                        # Terminal-style progress info
                        progress_text = f"[download] {percent*100:5.1f}% of {total_formatted:>10} at {speed_mbps:>6.2f}MiB/s ETA {eta_str}"
                        self.per_video_label.configure(text=progress_text)
                except (ValueError, TypeError):
                    pass
            elif d['status'] == 'finished':
                self.per_video_label.configure(text="Download finished, post-processing...")
                self.per_video_progress_bar.set(1.0)
        self.after(0, _update_gui)

    def update_postprocessor_display(self, d):
        def _update_gui():
            if d['status'] == 'started' or d['status'] == 'processing':
                self.per_video_label.configure(
                    text=f"Post-processing: {d.get('postprocessor')}")
            elif d['status'] == 'finished':
                self.per_video_label.configure(
                    text="Post-processing completed!")
                self.per_video_progress_bar.set(1.0)
        self.after(0, _update_gui)

    def log_to_gui(self, message): print(message)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
