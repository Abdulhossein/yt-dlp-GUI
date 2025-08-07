import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QPlainTextEdit, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtCore import QProcess, Qt


class YtDlpGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp GUI")
        self.resize(900, 600)

        # Menu bar with "Load Configuration" and "Update yt-dlp" actions
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        load_action = file_menu.addAction("Load Configuration...")
        load_action.triggered.connect(self.load_configuration)
        update_action = file_menu.addAction("Update yt-dlp")
        update_action.triggered.connect(self.update_yt_dlp)
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

        # Central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top panel for URL input and controls
        top_panel = QHBoxLayout()
        main_layout.addLayout(top_panel)
        top_panel.addWidget(QLabel("Video URL(s):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Enter one or multiple video URLs (separated by spaces or new lines)")
        top_panel.addWidget(self.url_input)
        # Button to browse for a batch file of URLs
        batch_btn = QPushButton("Batch File...")
        batch_btn.setToolTip(
            "Select a text file with URLs (one per line) to download (uses --batch-file)")
        batch_btn.clicked.connect(self.browse_batch_file)
        top_panel.addWidget(batch_btn)
        # Download button
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.start_download)
        top_panel.addWidget(download_btn)

        # Tab widget for option categories
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Dictionaries to map option names to widget controls for retrieval
        self.flag_widgets = {}   # for checkbox flags (no argument options)
        self.value_widgets = {}  # for options that take a value

        ##### General Options Tab #####
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        # --ignore-errors
        cb_ignore_errors = QCheckBox("Ignore errors (--ignore-errors)")
        cb_ignore_errors.setToolTip(
            "Ignore download and postprocessing errors. The download is considered successful even if postprocessing fails")
        self.flag_widgets["--ignore-errors"] = cb_ignore_errors
        general_layout.addRow(cb_ignore_errors)
        # --abort-on-error
        cb_abort_on_error = QCheckBox("Abort on error (--abort-on-error)")
        cb_abort_on_error.setToolTip(
            "Abort downloading further videos if an error occurs (stop on first error)")
        self.flag_widgets["--abort-on-error"] = cb_abort_on_error
        general_layout.addRow(cb_abort_on_error)
        # --ignore-config
        cb_ignore_config = QCheckBox("Ignore config files (--ignore-config)")
        cb_ignore_config.setToolTip(
            "Do not load any configuration files except those explicitly provided")
        self.flag_widgets["--ignore-config"] = cb_ignore_config
        general_layout.addRow(cb_ignore_config)
        # --flat-playlist
        cb_flat_playlist = QCheckBox("Flat playlist (do not fully extract)")
        cb_flat_playlist.setToolTip(
            "Do not extract each video in a playlist (list entries without detailed extraction)")
        self.flag_widgets["--flat-playlist"] = cb_flat_playlist
        general_layout.addRow(cb_flat_playlist)
        # --mark-watched
        cb_mark_watched = QCheckBox("Mark videos as watched (--mark-watched)")
        cb_mark_watched.setToolTip("Mark videos watched after downloading")
        self.flag_widgets["--mark-watched"] = cb_mark_watched
        general_layout.addRow(cb_mark_watched)
        # Color output control (represented as a "no color" checkbox for simplicity)
        cb_no_color = QCheckBox("No colored output (--color never)")
        cb_no_color.setToolTip(
            "Disable colorized output from yt-dlp (equivalent to --color \"never\")")
        # We'll handle this in command generation (not storing as flag directly)
        general_layout.addRow(cb_no_color)

        tabs.addTab(general_tab, "General")

        ##### Network Options Tab #####
        network_tab = QWidget()
        network_layout = QFormLayout(network_tab)
        # --proxy URL
        proxy_label = QLabel("Proxy URL:")
        proxy_label.setToolTip(
            "Use the specified HTTP/HTTPS/SOCKS proxy for downloads")
        edit_proxy = QLineEdit()
        edit_proxy.setPlaceholderText(
            "http://user:pass@proxy:port or socks5://...")
        edit_proxy.setToolTip(
            "Use the specified HTTP/HTTPS/SOCKS proxy for downloads. Leave blank for none")
        self.value_widgets["--proxy"] = edit_proxy
        network_layout.addRow(proxy_label, edit_proxy)
        # --socket-timeout SECONDS
        timeout_label = QLabel("Socket Timeout (s):")
        timeout_label.setToolTip("Time to wait before giving up, in seconds")
        edit_timeout = QLineEdit()
        edit_timeout.setPlaceholderText("Default is no timeout")
        edit_timeout.setToolTip(
            "Time (in seconds) to wait before timing out a network operation")
        self.value_widgets["--socket-timeout"] = edit_timeout
        network_layout.addRow(timeout_label, edit_timeout)
        # --source-address IP
        srcaddr_label = QLabel("Bind to IP:")
        srcaddr_label.setToolTip(
            "Client-side IP address to bind to (useful for multi-homed hosts)")
        edit_srcaddr = QLineEdit()
        edit_srcaddr.setPlaceholderText("e.g. 0.0.0.0")
        edit_srcaddr.setToolTip(
            "Client-side IP address to bind for outgoing connections. Leave blank to use default.")
        self.value_widgets["--source-address"] = edit_srcaddr
        network_layout.addRow(srcaddr_label, edit_srcaddr)
        # --force-ipv4 / --force-ipv6
        cb_ipv4 = QCheckBox("Force IPv4")
        cb_ipv4.setToolTip(
            "Make all connections via IPv4:contentReference[oaicite:146]{index=146}")
        self.flag_widgets["--force-ipv4"] = cb_ipv4
        network_layout.addRow(cb_ipv4)
        cb_ipv6 = QCheckBox("Force IPv6")
        cb_ipv6.setToolTip(
            "Make all connections via IPv6:contentReference[oaicite:147]{index=147}")
        self.flag_widgets["--force-ipv6"] = cb_ipv6
        network_layout.addRow(cb_ipv6)
        # --enable-file-urls
        cb_file_urls = QCheckBox("Enable file:// URLs")
        cb_file_urls.setToolTip(
            "Allow downloading from local file:// URLs (disabled by default for security):contentReference[oaicite:148]{index=148}")
        self.flag_widgets["--enable-file-urls"] = cb_file_urls
        network_layout.addRow(cb_file_urls)

        tabs.addTab(network_tab, "Network")

        ##### Video Selection Tab #####
        selection_tab = QWidget()
        selection_layout = QFormLayout(selection_tab)
        # --playlist-items ITEM_SPEC
        pl_items_label = QLabel("Playlist Items:")
        pl_items_label.setToolTip(
            "Download only specific items from a playlist (e.g. \"1-5,8\" or \"~10\" for last 10)")
        edit_pl_items = QLineEdit()
        edit_pl_items.setPlaceholderText("e.g. 1-3,5 or -10 (blank = all)")
        edit_pl_items.setToolTip(
            "Comma-separated indices of playlist items to download. Ranges like 1-3 or negative indices are supported")
        self.value_widgets["--playlist-items"] = edit_pl_items
        selection_layout.addRow(pl_items_label, edit_pl_items)
        # --min-filesize SIZE
        min_size_label = QLabel("Min Filesize:")
        min_size_label.setToolTip(
            "Skip downloads smaller than this size (e.g. 50k or 44.6M):contentReference[oaicite:151]{index=151}")
        edit_min_size = QLineEdit()
        edit_min_size.setPlaceholderText("e.g. 50M")
        edit_min_size.setToolTip(
            "Minimum file size to download. Videos smaller than this will be skipped:contentReference[oaicite:152]{index=152}")
        self.value_widgets["--min-filesize"] = edit_min_size
        selection_layout.addRow(min_size_label, edit_min_size)
        # --max-filesize SIZE
        max_size_label = QLabel("Max Filesize:")
        max_size_label.setToolTip(
            "Skip downloads larger than this size (e.g. 1G or 500m):contentReference[oaicite:153]{index=153}")
        edit_max_size = QLineEdit()
        edit_max_size.setPlaceholderText("e.g. 1G")
        edit_max_size.setToolTip(
            "Maximum file size to download. Videos larger than this will be skipped:contentReference[oaicite:154]{index=154}")
        self.value_widgets["--max-filesize"] = edit_max_size
        selection_layout.addRow(max_size_label, edit_max_size)
        # --date DATE
        date_label = QLabel("Upload Date:")
        date_label.setToolTip(
            "Download only videos uploaded on a specific date (YYYYMMDD or relative):contentReference[oaicite:155]{index=155}")
        edit_date = QLineEdit()
        edit_date.setPlaceholderText("YYYYMMDD or relative (e.g. today-7days)")
        edit_date.setToolTip(
            "Download only videos uploaded on this exact date or timespan:contentReference[oaicite:156]{index=156}")
        self.value_widgets["--date"] = edit_date
        selection_layout.addRow(date_label, edit_date)
        # --datebefore DATE
        datebefore_label = QLabel("Date Before:")
        datebefore_label.setToolTip(
            "Download only videos uploaded on or before this date:contentReference[oaicite:157]{index=157}")
        edit_datebefore = QLineEdit()
        edit_datebefore.setPlaceholderText("YYYYMMDD or relative date")
        edit_datebefore.setToolTip(
            "Latest upload date for videos to download (inclusive):contentReference[oaicite:158]{index=158}")
        self.value_widgets["--datebefore"] = edit_datebefore
        selection_layout.addRow(datebefore_label, edit_datebefore)
        # --dateafter DATE
        dateafter_label = QLabel("Date After:")
        dateafter_label.setToolTip(
            "Download only videos uploaded on or after this date:contentReference[oaicite:159]{index=159}")
        edit_dateafter = QLineEdit()
        edit_dateafter.setPlaceholderText("YYYYMMDD or relative date")
        edit_dateafter.setToolTip(
            "Earliest upload date for videos to download (inclusive):contentReference[oaicite:160]{index=160}")
        self.value_widgets["--dateafter"] = edit_dateafter
        selection_layout.addRow(dateafter_label, edit_dateafter)
        # --match-filters FILTER
        filter_label = QLabel("Match Filter:")
        filter_label.setToolTip(
            "Generic video filter by metadata (e.g. \"like_count>?100 & duration<?300\"):contentReference[oaicite:161]{index=161}")
        edit_filter = QLineEdit()
        edit_filter.setPlaceholderText("e.g. !is_live & like_count>?100")
        edit_filter.setToolTip(
            "A boolean expression to filter videos by metadata. Videos that don't match will be skipped:contentReference[oaicite:162]{index=162}")
        self.value_widgets["--match-filters"] = edit_filter
        selection_layout.addRow(filter_label, edit_filter)

        tabs.addTab(selection_tab, "Video Selection")

        ##### Download Options Tab #####
        download_tab = QWidget()
        download_layout = QFormLayout(download_tab)
        # -N, --concurrent-fragments N
        fragments_label = QLabel("Concurrent Fragments:")
        fragments_label.setToolTip(
            "Number of video fragments to download concurrently (for DASH/HLS, default is 1):contentReference[oaicite:163]{index=163}")
        edit_fragments = QLineEdit()
        edit_fragments.setPlaceholderText("Default 1")
        edit_fragments.setToolTip(
            "Number of fragments of a video to download in parallel (speeds up fragmented downloads):contentReference[oaicite:164]{index=164}")
        self.value_widgets["--concurrent-fragments"] = edit_fragments
        download_layout.addRow(fragments_label, edit_fragments)
        # -r, --limit-rate RATE
        rate_label = QLabel("Max Download Rate:")
        rate_label.setToolTip(
            "Maximum download rate (bytes/sec, e.g. 1M or 500K):contentReference[oaicite:165]{index=165}")
        edit_rate = QLineEdit()
        edit_rate.setPlaceholderText("e.g. 500K or 2M")
        edit_rate.setToolTip(
            "Limit the download speed to this rate. Leave blank for unlimited:contentReference[oaicite:166]{index=166}")
        self.value_widgets["--limit-rate"] = edit_rate
        download_layout.addRow(rate_label, edit_rate)
        # -R, --retries RETRIES
        retries_label = QLabel("Retries:")
        retries_label.setToolTip(
            "Number of download retries (default 10, or \"infinite\"):contentReference[oaicite:167]{index=167}")
        edit_retries = QLineEdit()
        edit_retries.setPlaceholderText("Default 10")
        edit_retries.setToolTip(
            "Number of retries for a download on error. \"infinite\" for unlimited retries:contentReference[oaicite:168]{index=168}")
        self.value_widgets["--retries"] = edit_retries
        download_layout.addRow(retries_label, edit_retries)
        # --fragment-retries RETRIES
        frag_retries_label = QLabel("Fragment Retries:")
        frag_retries_label.setToolTip(
            "Retries for a fragment download failure (default 10, or \"infinite\"):contentReference[oaicite:169]{index=169}")
        edit_frag_retries = QLineEdit()
        edit_frag_retries.setPlaceholderText("Default 10")
        edit_frag_retries.setToolTip(
            "How many times to retry a fragment download before giving up:contentReference[oaicite:170]{index=170}")
        self.value_widgets["--fragment-retries"] = edit_frag_retries
        download_layout.addRow(frag_retries_label, edit_frag_retries)
        # --buffer-size SIZE
        buffer_label = QLabel("Buffer Size:")
        buffer_label.setToolTip("Size of download buffer (e.g. 4K or 1M).")
        edit_buffer = QLineEdit()
        edit_buffer.setPlaceholderText("Default 1MiB")
        edit_buffer.setToolTip(
            "Size of the buffer for downloading. Adjust if needed to control memory usage or speed.")
        self.value_widgets["--buffer-size"] = edit_buffer
        download_layout.addRow(buffer_label, edit_buffer)
        # --no-part
        cb_no_part = QCheckBox("No .part files (--no-part)")
        cb_no_part.setToolTip(
            "Do not use temporary .part files; write directly to final file (risk of partial file on interruption).")
        self.flag_widgets["--no-part"] = cb_no_part
        download_layout.addRow(cb_no_part)
        # --wait-for-video MIN[-MAX]
        wait_label = QLabel("Wait for Scheduled:")
        wait_label.setToolTip(
            "Wait for scheduled streams to become available (min and optional max seconds between retries):contentReference[oaicite:171]{index=171}")
        edit_wait = QLineEdit()
        edit_wait.setPlaceholderText("e.g. 60 or 30-300")
        edit_wait.setToolTip(
            "If the video is scheduled (not yet live), wait this many seconds (or range) between retries:contentReference[oaicite:172]{index=172}")
        self.value_widgets["--wait-for-video"] = edit_wait
        download_layout.addRow(wait_label, edit_wait)

        tabs.addTab(download_tab, "Download")

        ##### Filesystem Options Tab #####
        filesystem_tab = QWidget()
        filesystem_layout = QFormLayout(filesystem_tab)
        # -a, --batch-file FILE
        batch_label = QLabel("Batch File:")
        batch_label.setToolTip(
            "File containing URLs to download (one per line):contentReference[oaicite:173]{index=173}")
        edit_batch = QLineEdit()
        edit_batch.setPlaceholderText("Select a file containing URLs")
        edit_batch.setToolTip(
            "Path to a text file with one URL per line to download. Use the 'Batch File...' button to select:contentReference[oaicite:174]{index=174}")
        self.value_widgets["--batch-file"] = edit_batch
        filesystem_layout.addRow(batch_label, edit_batch)
        # -o, --output TEMPLATE
        output_label = QLabel("Output Template:")
        output_label.setToolTip(
            "Template for output filenames (see yt-dlp documentation for template fields)")
        edit_output = QLineEdit()
        edit_output.setPlaceholderText("%(title)s.%(ext)s (default)")
        edit_output.setToolTip(
            "Output filename template using yt-dlp format specifiers. Leave blank for default (title.ext)")
        # using "-o" to denote output template
        self.value_widgets["-o"] = edit_output
        filesystem_layout.addRow(output_label, edit_output)
        # Output directory (not a direct yt-dlp option, will prepend to -o template if used)
        outdir_label = QLabel("Output Directory:")
        outdir_label.setToolTip("Directory to save downloads in")
        self.outdir_edit = QLineEdit()
        self.outdir_edit.setPlaceholderText("Browse for folder...")
        self.outdir_edit.setToolTip(
            "Select a directory to save files. If set, the output template will be relative to this directory.")
        browse_outdir_btn = QPushButton("Browse...")

        def choose_outdir():
            d = QFileDialog.getExistingDirectory(
                self, "Select Download Directory")
            if d:
                self.outdir_edit.setText(d)
        browse_outdir_btn.clicked.connect(choose_outdir)
        outdir_row = QHBoxLayout()
        outdir_row.addWidget(self.outdir_edit)
        outdir_row.addWidget(browse_outdir_btn)
        filesystem_layout.addRow(outdir_label, outdir_row)
        # --restrict-filenames
        cb_restrict_names = QCheckBox("Restrict filenames")
        cb_restrict_names.setToolTip(
            "Restrict output filenames to ASCII characters and remove spaces (for compatibility)")
        self.flag_widgets["--restrict-filenames"] = cb_restrict_names
        filesystem_layout.addRow(cb_restrict_names)
        # --no-overwrites
        cb_no_overwrite = QCheckBox("Do not overwrite files (--no-overwrites)")
        cb_no_overwrite.setToolTip(
            "Do not overwrite existing files (skip download if file already exists)")
        self.flag_widgets["--no-overwrites"] = cb_no_overwrite
        filesystem_layout.addRow(cb_no_overwrite)
        # --windows-filenames
        cb_windows_names = QCheckBox("Windows-safe filenames")
        cb_windows_names.setToolTip(
            "Force filenames to be Windows-compatible (avoid characters like : ? * < > |)")
        self.flag_widgets["--windows-filenames"] = cb_windows_names
        filesystem_layout.addRow(cb_windows_names)

        tabs.addTab(filesystem_tab, "Filesystem")

        ##### Format Options Tab #####
        format_tab = QWidget()
        format_layout = QFormLayout(format_tab)
        # -f, --format FORMAT
        format_label = QLabel("Format selection:")
        format_label.setToolTip(
            "Video format code or criteria (e.g. 'bestvideo+bestaudio' or 'mp4')")
        edit_format = QLineEdit()
        edit_format.setPlaceholderText("e.g. best or 137+bestaudio")
        edit_format.setToolTip(
            "Format code or selection expression. Leave blank for default (best available quality).")
        self.value_widgets["--format"] = edit_format
        format_layout.addRow(format_label, edit_format)
        # -S, --format-sort SORTORDER
        sort_label = QLabel("Format sort:")
        sort_label.setToolTip(
            "Sort order for formats (e.g. 'res,br' to sort by resolution then bitrate)")
        edit_sort = QLineEdit()
        edit_sort.setPlaceholderText("e.g. res, size, br")
        edit_sort.setToolTip("Criteria to sort available formats by preference (e.g. 'resolution' or 'codec')"
                             " - see yt-dlp docs for format sorting.")
        self.value_widgets["--format-sort"] = edit_sort
        format_layout.addRow(sort_label, edit_sort)
        # --merge-output-format FORMAT
        merge_label = QLabel("Merge output into:")
        merge_label.setToolTip(
            "Container format to use when merging video+audio (e.g. mp4, mkv)")
        edit_merge = QLineEdit()
        edit_merge.setPlaceholderText("mp4/mkv")
        edit_merge.setToolTip(
            "Specify a container format for merged downloads (only used if merging separate video/audio files)")
        self.value_widgets["--merge-output-format"] = edit_merge
        format_layout.addRow(merge_label, edit_merge)
        # --no-check-certificates (placed here as an advanced network setting)
        cb_no_cert = QCheckBox(
            "Skip HTTPS cert verify (--no-check-certificates)")
        cb_no_cert.setToolTip(
            "Do not verify SSL certificates (use only if necessary; security risk)")
        self.flag_widgets["--no-check-certificates"] = cb_no_cert
        format_layout.addRow(cb_no_cert)

        tabs.addTab(format_tab, "Format")

        ##### Subtitle Options Tab #####
        subs_tab = QWidget()
        subs_layout = QFormLayout(subs_tab)
        # --write-subs
        cb_write_subs = QCheckBox("Download subtitles (--write-subs)")
        cb_write_subs.setToolTip(
            "Write subtitle file for the video (if available)")
        self.flag_widgets["--write-subs"] = cb_write_subs
        subs_layout.addRow(cb_write_subs)
        # --write-auto-subs
        cb_write_auto = QCheckBox("Download auto-generated subs")
        cb_write_auto.setToolTip(
            "Include automatically generated subtitles (YouTube auto-captions)")
        self.flag_widgets["--write-auto-subs"] = cb_write_auto
        subs_layout.addRow(cb_write_auto)
        # --sub-langs
        sublang_label = QLabel("Subtitle Languages:")
        sublang_label.setToolTip(
            "Languages of subtitles to download (comma-separated or \"all\")")
        edit_sublang = QLineEdit()
        edit_sublang.setPlaceholderText("e.g. en,fr or all")
        edit_sublang.setToolTip(
            "Comma-separated list of subtitle language codes to download (e.g. \"en,ja\" or \"all\").")
        self.value_widgets["--sub-langs"] = edit_sublang
        subs_layout.addRow(sublang_label, edit_sublang)
        # --sub-format
        subformat_label = QLabel("Subtitle Format:")
        subformat_label.setToolTip("Preferred subtitle format (e.g. srt, ass)")
        edit_subformat = QLineEdit()
        edit_subformat.setPlaceholderText("e.g. srt or best")
        edit_subformat.setToolTip(
            "Subtitle format or priority list of formats (e.g. \"ass/srt/best\"). Default is best available.")
        self.value_widgets["--sub-format"] = edit_subformat
        subs_layout.addRow(subformat_label, edit_subformat)
        # --embed-subs
        cb_embed_subs = QCheckBox("Embed subtitles in video")
        cb_embed_subs.setToolTip(
            "Embed downloaded subtitles into the video file (requires ffmpeg)")
        self.flag_widgets["--embed-subs"] = cb_embed_subs
        subs_layout.addRow(cb_embed_subs)
        # --embed-thumbnail
        cb_embed_thumb = QCheckBox("Embed thumbnail")
        cb_embed_thumb.setToolTip(
            "Embed thumbnail image into the video as cover art (where applicable)")
        self.flag_widgets["--embed-thumbnail"] = cb_embed_thumb
        subs_layout.addRow(cb_embed_thumb)

        tabs.addTab(subs_tab, "Subtitles")

        ##### Post-Processing Options Tab #####
        post_tab = QWidget()
        post_layout = QFormLayout(post_tab)
        # -x, --extract-audio
        cb_extract_audio = QCheckBox("Extract audio only (-x)")
        cb_extract_audio.setToolTip(
            "Convert video files to audio-only files (requires ffmpeg)")
        self.flag_widgets["--extract-audio"] = cb_extract_audio
        post_layout.addRow(cb_extract_audio)
        # --audio-format
        audio_format_label = QLabel("Audio format:")
        audio_format_label.setToolTip(
            "Format to convert audio to when extracting (e.g. mp3, m4a)")
        edit_audio_format = QLineEdit()
        edit_audio_format.setPlaceholderText("best (default) or mp3/opus/etc")
        edit_audio_format.setToolTip(
            "Desired audio format for extracted audio. E.g. \"mp3\" or \"m4a\" (default is best quality)")
        self.value_widgets["--audio-format"] = edit_audio_format
        post_layout.addRow(audio_format_label, edit_audio_format)
        # --audio-quality
        audio_q_label = QLabel("Audio quality:")
        audio_q_label.setToolTip(
            "ffmpeg audio quality (0=best, 10=worst, or a bitrate like 128K)")
        edit_audio_q = QLineEdit()
        edit_audio_q.setPlaceholderText("0-10 or bitrate (128K)")
        edit_audio_q.setToolTip(
            "Audio quality setting for ffmpeg when converting audio. 0 = best, 10 = worst, or specify bitrate")
        self.value_widgets["--audio-quality"] = edit_audio_q
        post_layout.addRow(audio_q_label, edit_audio_q)
        # --remux-video
        remux_label = QLabel("Remux video to:")
        remux_label.setToolTip(
            "Remux (repackage) video into another container if needed (e.g. mp4, mkv)")
        edit_remux = QLineEdit()
        edit_remux.setPlaceholderText("e.g. mp4 or mkv")
        edit_remux.setToolTip(
            "If the downloaded video is not in the desired container, remux it (no re-encoding). E.g. \"mp4\" to ensure MP4 container")
        self.value_widgets["--remux-video"] = edit_remux
        post_layout.addRow(remux_label, edit_remux)
        # --recode-video
        recode_label = QLabel("Re-encode video to:")
        recode_label.setToolTip(
            "Re-encode the video into another format if necessary (e.g. mp4, avi, etc.)")
        edit_recode = QLineEdit()
        edit_recode.setPlaceholderText("e.g. mp4 or avi")
        edit_recode.setToolTip(
            "Force re-encoding of the video to the specified format after download (use if remux is not enough)")
        self.value_widgets["--recode-video"] = edit_recode
        post_layout.addRow(recode_label, edit_recode)
        # --embed-metadata
        cb_embed_metadata = QCheckBox("Embed metadata")
        cb_embed_metadata.setToolTip(
            "Embed metadata to the video (title, artist, etc.), including chapters unless disabled")
        self.flag_widgets["--embed-metadata"] = cb_embed_metadata
        post_layout.addRow(cb_embed_metadata)
        # --embed-chapters
        cb_embed_chapters = QCheckBox("Embed chapters")
        cb_embed_chapters.setToolTip(
            "Add chapter markers to the video file (if present in metadata)")
        self.flag_widgets["--embed-chapters"] = cb_embed_chapters
        post_layout.addRow(cb_embed_chapters)
        # --embed-info-json
        cb_embed_infojson = QCheckBox("Embed info JSON")
        cb_embed_infojson.setToolTip(
            "Embed the info.json as an attachment to the output file (for mkv/mka)")
        self.flag_widgets["--embed-info-json"] = cb_embed_infojson
        post_layout.addRow(cb_embed_infojson)
        # -k, --keep-video
        cb_keep_video = QCheckBox("Keep original video file")
        cb_keep_video.setToolTip(
            "Keep the original video file on disk after post-processing")
        self.flag_widgets["--keep-video"] = cb_keep_video
        post_layout.addRow(cb_keep_video)
        # --no-post-overwrites
        cb_no_post_overwrite = QCheckBox("No post-process overwrites")
        cb_no_post_overwrite.setToolTip(
            "Do not overwrite files that have already been post-processed")
        self.flag_widgets["--no-post-overwrites"] = cb_no_post_overwrite
        post_layout.addRow(cb_no_post_overwrite)

        tabs.addTab(post_tab, "Post-processing")

        ##### Authentication Options Tab #####
        auth_tab = QWidget()
        auth_layout = QFormLayout(auth_tab)
        # -u, --username
        user_label = QLabel("Username:")
        user_label.setToolTip(
            "Login username for sites that require authentication")
        edit_user = QLineEdit()
        edit_user.setPlaceholderText("Account login")
        edit_user.setToolTip(
            "Account username for authentication-required downloads (leave blank if not needed)")
        self.value_widgets["--username"] = edit_user
        auth_layout.addRow(user_label, edit_user)
        # -p, --password
        pass_label = QLabel("Password:")
        pass_label.setToolTip("Account password (will prompt if not provided)")
        edit_pass = QLineEdit()
        edit_pass.setPlaceholderText("Account password")
        edit_pass.setEchoMode(QLineEdit.Password)
        edit_pass.setToolTip(
            "Account password for login. If left blank and required, yt-dlp will prompt in console")
        self.value_widgets["--password"] = edit_pass
        auth_layout.addRow(pass_label, edit_pass)
        # -2, --twofactor
        twofactor_label = QLabel("2FA code:")
        twofactor_label.setToolTip(
            "Two-factor authentication code (if required)")
        edit_twofactor = QLineEdit()
        edit_twofactor.setPlaceholderText("Two-factor code")
        edit_twofactor.setToolTip(
            "Two-factor authentication code for login (if applicable)")
        self.value_widgets["--twofactor"] = edit_twofactor
        auth_layout.addRow(twofactor_label, edit_twofactor)
        # -n, --netrc
        cb_netrc = QCheckBox("Use .netrc for auth")
        cb_netrc.setToolTip(
            "Use ~/.netrc file for authentication (instead of specifying username/password)")
        self.flag_widgets["--netrc"] = cb_netrc
        auth_layout.addRow(cb_netrc)
        # --video-password
        video_pass_label = QLabel("Video Password:")
        video_pass_label.setToolTip(
            "Password for encrypted or private video (if any)")
        edit_video_pass = QLineEdit()
        edit_video_pass.setPlaceholderText("Video password (if needed)")
        edit_video_pass.setToolTip(
            "Video-specific password for accessing private videos")
        self.value_widgets["--video-password"] = edit_video_pass
        auth_layout.addRow(video_pass_label, edit_video_pass)
        # (Skipping some advanced authentication options for brevity)

        tabs.addTab(auth_tab, "Authentication")

        ##### Advanced Tab (SponsorBlock, Verbosity, Workarounds, etc.) #####
        adv_tab = QWidget()
        adv_layout = QFormLayout(adv_tab)
        # SponsorBlock (not individual options but we mention categories for demonstration)
        sb_label = QLabel("SponsorBlock (remove segments):")
        sb_label.setToolTip(
            "Select types of segments to remove using SponsorBlock API (YouTube only):contentReference[oaicite:213]{index=213}")
        adv_layout.addRow(sb_label)
        cb_sb_sponsor = QCheckBox("Sponsors")
        cb_sb_sponsor.setToolTip(
            "Remove sponsored segments from videos using SponsorBlock")
        cb_sb_intros = QCheckBox("Introductions")
        cb_sb_intros.setToolTip(
            "Remove introduction segments from videos using SponsorBlock")
        adv_layout.addRow(cb_sb_sponsor)
        adv_layout.addRow(cb_sb_intros)
        # Verbosity & Simulation
        cb_quiet = QCheckBox("Quiet mode (-q)")
        cb_quiet.setToolTip(
            "Minimal output mode (no progress bar or info). Combine with -v to log to stderr")
        self.flag_widgets["--quiet"] = cb_quiet
        adv_layout.addRow(cb_quiet)
        cb_verbose = QCheckBox("Verbose mode (-v)")
        cb_verbose.setToolTip("Print debugging information (verbose output)")
        self.flag_widgets["--verbose"] = cb_verbose
        adv_layout.addRow(cb_verbose)
        cb_dump_pages = QCheckBox("Dump pages (--dump-pages)")
        cb_dump_pages.setToolTip(
            "Write downloaded intermediary pages to files (for debugging)")
        self.flag_widgets["--dump-pages"] = cb_dump_pages
        adv_layout.addRow(cb_dump_pages)
        cb_console_title = QCheckBox("Console title progress")
        cb_console_title.setToolTip(
            "Display progress in console window title bar (console only, for completeness)")
        self.flag_widgets["--console-title"] = cb_console_title
        adv_layout.addRow(cb_console_title)
        # Workarounds
        cb_prefer_insecure = QCheckBox("Prefer insecure HTTP")
        cb_prefer_insecure.setToolTip(
            "Use an unencrypted connection (HTTP) to retrieve info when possible")
        self.flag_widgets["--prefer-insecure"] = cb_prefer_insecure
        adv_layout.addRow(cb_prefer_insecure)
        cb_legacy_connect = QCheckBox("Legacy server connect")
        cb_legacy_connect.setToolTip(
            "Allow HTTPS connections to servers without secure renegotiation (legacy support)")
        self.flag_widgets["--legacy-server-connect"] = cb_legacy_connect
        adv_layout.addRow(cb_legacy_connect)
        cb_bidi_workaround = QCheckBox("Bidirectional text fix")
        cb_bidi_workaround.setToolTip(
            "Work around terminals that lack bidirectional text support (requires bidiv/fribidi)")
        self.flag_widgets["--bidi-workaround"] = cb_bidi_workaround
        adv_layout.addRow(cb_bidi_workaround)

        tabs.addTab(adv_tab, "Advanced")

        # Log output text area
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(1000)
        main_layout.addWidget(self.log_output)
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)

        # QProcess for running yt-dlp
        self.process = None

        # Preserve the no_color checkbox (not stored in flag_widgets) by linking it to a variable
        self.no_color_checkbox = cb_no_color

    def browse_batch_file(self):
        """Open a file dialog to select a batch file of URLs and set it in the batch-file field."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Batch File", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            if "--batch-file" in self.value_widgets:
                self.value_widgets["--batch-file"].setText(filepath)
            else:
                # If batch-file option is not present in UI (should be), fallback: load into URL field
                try:
                    with open(filepath, 'r') as f:
                        urls = [line.strip() for line in f if line.strip()
                                and not line.startswith('#')]
                    if urls:
                        self.url_input.setText(" ".join(urls))
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", f"Could not load batch file: {e}")

    def start_download(self):
        """Collect selected options and start the yt-dlp download process."""
        urls_text = self.url_input.text().strip()
        if not urls_text and not self.value_widgets.get("--batch-file", QLineEdit()).text():
            QMessageBox.warning(
                self, "No URL", "Please enter at least one video URL or specify a batch file.")
            return

        cmd = ["yt-dlp"]
        # Add flag options (checkboxes)
        for opt, widget in self.flag_widgets.items():
            if isinstance(widget, QCheckBox) and widget.isChecked():
                cmd.append(opt)
        # Handle special case for no_color checkbox
        if hasattr(self, 'no_color_checkbox') and self.no_color_checkbox.isChecked():
            cmd += ["--color", "never"]
        # Add value options (text fields)
        # Handle output directory combination with -o
        output_dir_text = self.outdir_edit.text().strip() if hasattr(self,
                                                                     'outdir_edit') else ""
        template_text = self.value_widgets.get(
            "-o", QLineEdit()).text().strip() if "-o" in self.value_widgets else ""
        if output_dir_text:
            if template_text:
                if "/" in template_text or "\\" in template_text:
                    combined_template = template_text
                else:
                    combined_template = f"{output_dir_text}/{template_text}"
            else:
                combined_template = f"{output_dir_text}/%(title)s.%(ext)s"
            cmd += ["-o", combined_template]
        else:
            if template_text:
                cmd += ["-o", template_text]
        for opt, widget in self.value_widgets.items():
            if opt == "-o":
                continue  # already handled
            if isinstance(widget, QLineEdit):
                val = widget.text().strip()
                if val:
                    cmd.append(opt)
                    cmd.append(val)
        # Append URLs
        if urls_text:
            urls = urls_text.split()
            cmd += urls

        # Start the QProcess for yt-dlp
        if self.process:
            QMessageBox.information(
                self, "Download in progress", "Another download is currently running. Please wait.")
            return
        self.log_output.clear()
        self.progress_bar.setValue(0)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_process_output)
        self.process.finished.connect(self._on_process_finished)
        try:
            self.process.start(cmd[0], cmd[1:])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start yt-dlp: {e}")
            self.process = None

    def _on_process_output(self):
        """Read output from yt-dlp process and update log and progress bar."""
        if not self.process:
            return
        data = self.process.readAllStandardOutput()
        if not data:
            return
        text = bytes(data).decode('utf-8', errors='ignore')
        if text:
            self.log_output.appendPlainText(text.strip())
            match = re.search(r'(\d{1,3}(?:\.\d+)?)%', text)
            if match:
                try:
                    percent = float(match.group(1))
                    if 0 <= percent <= 100:
                        self.progress_bar.setValue(int(percent))
                except:
                    pass

    def _on_process_finished(self, exitCode, exitStatus):
        """Handle process completion."""
        if exitStatus == QProcess.CrashExit:
            self.log_output.appendPlainText(
                "Download process terminated unexpectedly.")
        else:
            self.log_output.appendPlainText("Download completed.")
            self.progress_bar.setValue(100)
        self.process = None

    def load_configuration(self):
        """Load options from a yt-dlp configuration file into the GUI."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Configuration File", "", "Config Files (*.conf *.txt);;All Files (*)")
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to open config file: {e}")
            return
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(maxsplit=1)
            opt = parts[0]
            val = parts[1] if len(parts) > 1 else None
            # Apply to GUI if option is known
            if opt in self.flag_widgets and isinstance(self.flag_widgets[opt], QCheckBox):
                if val is None:
                    self.flag_widgets[opt].setChecked(True)
            if opt in self.value_widgets and isinstance(self.value_widgets[opt], QLineEdit):
                if val is not None:
                    val_clean = val.strip().strip('"')
                    self.value_widgets[opt].setText(val_clean)
            # Handle short options mapping to long
            short_map = {
                "-i": "--ignore-errors", "-q": "--quiet", "-s": "--simulate", "-j": "--dump-json",
                "-J": "--dump-single-json", "-v": "--verbose", "-u": "--username", "-p": "--password",
                "-a": "--batch-file", "-o": "--output", "-f": "--format", "-S": "--format-sort",
                "-R": "--retries", "-4": "--force-ipv4", "-6": "--force-ipv6", "-x": "--extract-audio",
            }
            if opt in short_map:
                long_opt = short_map[opt]
                if long_opt in self.flag_widgets and val is None:
                    self.flag_widgets[long_opt].setChecked(True)
                if long_opt in self.value_widgets and val is not None:
                    val_clean = val.strip().strip('"')
                    self.value_widgets[long_opt].setText(val_clean)
        QMessageBox.information(self, "Configuration Loaded",
                                "Configuration options have been applied to the GUI.")

    def update_yt_dlp(self):
        """Run yt-dlp self-update and display result."""
        proc = QProcess(self)
        proc.start("yt-dlp", ["-U"])
        proc.waitForFinished(5000)
        output = bytes(proc.readAllStandardOutput()).decode(
            'utf-8', errors='ignore')
        if output:
            self.log_output.appendPlainText(output.strip())
        QMessageBox.information(self, "yt-dlp Update",
                                "yt-dlp has been updated. See log for details.")

    def show_about(self):
        QMessageBox.about(self, "About yt-dlp GUI",
                          "yt-dlp GUI\nA graphical user interface for yt-dlp.\n\n"
                          "Allows downloading videos with ease, exposing advanced options in a friendly way.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = YtDlpGUI()
    gui.show()
    sys.exit(app.exec_())
