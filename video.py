import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import cv2  # OpenCV for video decoding
import threading
import time
import collections  # For deque for buffering
import os

# For audio
import sounddevice as sd  # Using sounddevice instead of pyaudio
import ffmpeg  # For efficient audio extraction directly from video
from ffmpeg import probe, Error  # Explicitly import probe and Error
import numpy as np  # For potential audio data manipulation, especially with sounddevice

# Constants for buffering
PRE_BUFFER_SECONDS = 5  # Try to buffer this many seconds ahead of current playback for video/audio
POST_UNLOAD_SECONDS = 10  # Unload frames/audio this many seconds behind current position
MAX_BUFFER_SIZE_FRAMES = 500  # Max number of frames to keep in video buffer (approx 15-20s at 30fps)
MAX_AUDIO_BUFFER_SIZE_CHUNKS = 100  # Max number of audio chunks (adjust based on chunk size and needed buffer)

# Audio specific constants
AUDIO_CHUNK_FRAMES = 1024  # A common buffer size for sounddevice callbacks. Adjust if needed.
AUDIO_FORMAT = 'int16'  # sounddevice uses string for format
AUDIO_CHANNELS = 2  # Stereo (usually)
AUDIO_SAMPLE_RATE = 44100  # Standard sample rate


class VideoPlayer(Gtk.Window):
    def __init__(self):
        super().__init__(title="My Custom Video Player (No GStreamer)")
        self.set_default_size(800, 600)
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key_press)

        self.video_capture = None
        self.audio_process = None  # ffmpeg process for audio extraction
        self.audio_stream = None  # sounddevice stream

        self.frame_buffer = collections.deque()  # Thread-safe deque for video frames
        # audio_buffer now stores raw bytes from ffmpeg, not pydub segments
        self.audio_buffer = collections.deque()  # Thread-safe deque for audio chunks (bytes)
        self.buffer_lock = threading.Lock()  # Lock for accessing both buffers

        self.playback_running = False  # Controls the rendering loop
        self.buffering_running = False  # Controls the buffering thread
        self.buffering_thread = None

        self.current_frame_number = 0
        self.total_frames = 0
        self.fps = 0
        self.video_duration_s = 0

        self.current_audio_ms = 0  # Current position in milliseconds for audio
        self.total_audio_ms = 0  # Total audio duration in milliseconds
        self.total_audio_bytes = 0  # Track total audio bytes for seeking accuracy

        self.playback_timer_id = None  # For scheduling frame draws
        self._frame_for_drawing = None  # Holds the frame to be drawn by on_video_area_draw

        self.main_vbox = Gtk.VBox(spacing=6)
        self.add(self.main_vbox)

        self.create_menu()
        self.create_ui_elements()

    def create_menu(self):
        menubar = Gtk.MenuBar()
        self.main_vbox.pack_start(menubar, False, False, 0)

        file_menu_item = Gtk.MenuItem(label="File")
        file_menu = Gtk.Menu()
        file_menu_item.set_submenu(file_menu)

        open_video_item = Gtk.MenuItem(label="Open Video")
        open_video_item.connect("activate", self.on_open_video)
        file_menu.append(open_video_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_destroy)
        file_menu.append(quit_item)

        menubar.append(file_menu_item)

    def create_ui_elements(self):
        self.video_area = Gtk.DrawingArea()
        self.video_area.set_size_request(640, 480)
        self.video_area.set_hexpand(True)
        self.video_area.set_vexpand(True)
        self.main_vbox.pack_start(self.video_area, True, True, 0)

        self.video_area.connect("draw", self.on_video_area_draw)
        self.video_area.connect("size-allocate", self.on_video_area_size_allocate)

        control_box = Gtk.HBox(spacing=6)
        self.main_vbox.pack_start(control_box, False, False, 0)

        self.play_pause_button = Gtk.Button(label="▶ Play")
        self.play_pause_button.connect("clicked", self.on_play_pause_clicked)
        control_box.pack_start(self.play_pause_button, False, False, 0)

        self.timeline_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.timeline_scale.set_hexpand(True)
        self.timeline_scale.set_draw_value(False)
        self.timeline_scale_handler_id = self.timeline_scale.connect("value-changed", self.on_timeline_changed)
        self.timeline_scale.connect("button-release-event", self.on_timeline_released)
        control_box.pack_start(self.timeline_scale, True, True, 0)

        self.time_label = Gtk.Label(label="00:00 / 00:00")
        control_box.pack_start(self.time_label, False, False, 0)

    def on_video_area_draw(self, widget, cr):
        if self._frame_for_drawing is not None:
            frame_to_draw = self._frame_for_drawing

            h, w, c = frame_to_draw.shape
            img_rgb = cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB)

            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                img_rgb.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                w, h,
                w * c
            )

            allocation = self.video_area.get_allocation()
            area_width = allocation.width
            area_height = allocation.height

            scale_w = area_width / w
            scale_h = area_height / h
            scale = min(scale_w, scale_h)

            scaled_w = int(w * scale)
            scaled_h = int(h * scale)

            x_offset = (area_width - scaled_w) // 2
            y_offset = (area_height - scaled_h) // 2

            cr.set_source_rgb(0, 0, 0)
            cr.paint()

            Gdk.cairo_set_source_pixbuf(cr, pixbuf.scale_simple(scaled_w, scaled_h, GdkPixbuf.InterpType.BILINEAR),
                                        x_offset, y_offset)
            cr.rectangle(x_offset, y_offset, scaled_w, scaled_h)
            cr.fill()

            self._frame_for_drawing = None
            return True

        else:
            cr.set_source_rgb(0, 0, 0)
            cr.paint()
            return False

    def on_video_area_size_allocate(self, widget, allocation):
        self.video_area.queue_draw()

    def on_open_video(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Open Video File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_video = Gtk.FileFilter()
        filter_video.set_name("Video Files")
        filter_video.add_mime_type("video/*")
        filter_video.add_pattern("*.mp4")
        filter_video.add_pattern("*.avi")
        filter_video.add_pattern("*.mkv")
        dialog.add_filter(filter_video)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            print(f"Selected video: {filepath}")
            self.load_video(filepath)
        else:
            print("File selection cancelled.")

        dialog.destroy()

    def load_video(self, filepath):
        if not filepath:
            print("No filepath provided to load_video.")
            return

        # Stop previous video and threads
        self._stop_playback()
        self._stop_buffering()
        self._close_audio_stream()

        self.video_capture = cv2.VideoCapture(filepath)
        if not self.video_capture.isOpened():
            print(f"ERROR: Could not open video file: {filepath}")
            self.play_pause_button.set_label("▶ Play")
            self.timeline_scale.set_range(0, 100)
            self.timeline_scale.set_value(0)
            self.time_label.set_label("00:00 / 00:00")
            return

        self.current_filepath = filepath
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration_s = self.total_frames / self.fps if self.fps > 0 else 0

        # --- Audio Loading (using ffmpeg-python) ---
        print(f"Preparing audio stream from {filepath} with ffmpeg...")
        try:
            # Probe video for audio stream info (duration, sample rate, channels)
            probe_result = probe(filepath)  # Use the imported probe
            audio_stream_info = next((s for s in probe_result['streams'] if s['codec_type'] == 'audio'), None)

            if audio_stream_info:
                # Get actual audio duration from stream info if available
                # Fallback to video duration if audio duration not explicitly in stream info
                self.total_audio_ms = float(audio_stream_info.get('duration', self.video_duration_s)) * 1000

                # Setup ffmpeg command to output raw PCM audio
                # Ensure correct format for sounddevice ('s16le' for int16 little-endian)
                ffmpeg_args = {
                    'format': 's16le',  # Signed 16-bit little-endian PCM
                    'acodec': 'pcm_s16le',  # Force PCM S16LE codec
                    'ac': AUDIO_CHANNELS,  # Number of channels
                    'ar': AUDIO_SAMPLE_RATE  # Sample rate
                }

                # Start ffmpeg process for audio extraction
                # It will read the entire audio stream, this might be slow for very long videos initially
                # For seeking, we'll restart this process with a -ss flag
                self.audio_process = (
                    ffmpeg
                    .input(filepath)
                    .output('pipe:', **ffmpeg_args)
                    .run_async(pipe_stdout=True)
                )
                print(f"FFmpeg audio extraction process started. Duration={self.total_audio_ms / 1000:.2f}s")
                # Calculate expected total audio bytes for buffering/seeking accuracy
                # 2 bytes per sample for int16, AUDIO_CHANNELS channels
                self.total_audio_bytes = int(
                    self.total_audio_ms / 1000 * AUDIO_SAMPLE_RATE * AUDIO_CHANNELS * np.dtype(AUDIO_FORMAT).itemsize)

            else:
                print("No audio stream found in video file.")
                self.audio_process = None
                self.total_audio_ms = 0
                self.total_audio_bytes = 0

        except Error as e:  # Use the imported Error
            print(f"FFmpeg Error: {e.stderr.decode()}")
            self.audio_process = None
            self.total_audio_ms = 0
            self.total_audio_bytes = 0
        except Exception as e:
            print(f"ERROR: Could not prepare audio stream with ffmpeg: {e}")
            self.audio_process = None
            self.total_audio_ms = 0
            self.total_audio_bytes = 0

        print(f"Video loaded: FPS={self.fps}, Total Frames={self.total_frames}, Duration={self.video_duration_s:.2f}s")

        self.timeline_scale.set_range(0, 100)
        self.timeline_scale.set_value(0)
        self.time_label.set_label("00:00 / 00:00")
        self.play_pause_button.set_label("▶ Play")

        self.current_frame_number = 0
        self.current_audio_ms = 0
        with self.buffer_lock:
            self.frame_buffer.clear()
            self.audio_buffer.clear()
            self._frame_for_drawing = None

        # Start the buffering thread
        self.buffering_running = True
        self.buffering_thread = threading.Thread(target=self._media_buffering_thread, args=(filepath,))
        self.buffering_thread.daemon = True
        self.buffering_thread.start()

        # Give buffering thread a moment to fill some initial data
        time.sleep(0.2)  # Adjusted sleep time for initial buffer

        # Initial playback state is paused
        self.playback_running = False
        self.play_pause_button.set_label("▶ Play")

        # Request initial draw to show the first frame
        self.video_area.queue_draw()
        # Update timeline once
        self.update_timeline_and_label()

    def _media_buffering_thread(self, filepath):
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            print(f"Buffering thread: Could not open video file {filepath}")
            self.buffering_running = False
            return

        print(f"Buffering thread: Starting...")

        # Determine bytes per audio sample for calculation
        bytes_per_sample = np.dtype(AUDIO_FORMAT).itemsize
        bytes_per_audio_frame = AUDIO_CHANNELS * bytes_per_sample
        # Calculate how many bytes constitute one chunk of AUDIO_CHUNK_FRAMES
        audio_chunk_bytes_size = AUDIO_CHUNK_FRAMES * bytes_per_audio_frame

        while self.buffering_running:
            with self.buffer_lock:
                # --- Video Buffering Logic ---
                playback_frame = self.current_frame_number
                # Get the last frame number in the buffer, or the current playback frame - 1 if buffer is empty
                last_buffered_frame_num = self.frame_buffer[-1][0] if len(self.frame_buffer) > 0 else playback_frame - 1
                desired_frames_ahead = int(self.fps * PRE_BUFFER_SECONDS)
                next_read_frame_num = last_buffered_frame_num + 1

                if (len(self.frame_buffer) < MAX_BUFFER_SIZE_FRAMES and
                        (last_buffered_frame_num < playback_frame + desired_frames_ahead) and
                        next_read_frame_num < self.total_frames):

                    current_cap_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                    if current_cap_pos != next_read_frame_num:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, next_read_frame_num)

                    ret, frame = cap.read()
                    if ret:
                        frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                        if frame_num >= 0:
                            self.frame_buffer.append((frame_num, frame))
                    else:  # No more video frames to read
                        if next_read_frame_num >= self.total_frames:
                            # print("Buffering thread: No more video frames to read.")
                            pass  # Keep buffering_running True as audio might still need buffering

                # --- Audio Buffering Logic (from ffmpeg process) ---
                if self.audio_process and not self.audio_process.poll():  # Check if ffmpeg process is still running
                    # Check if audio buffer needs refilling
                    playback_audio_byte_pos = int(
                        self.current_audio_ms / 1000 * AUDIO_SAMPLE_RATE * bytes_per_audio_frame)

                    last_buffered_audio_byte_pos = 0
                    if len(self.audio_buffer) > 0:
                        # The tuple is (start_byte_offset, raw_data_chunk)
                        last_buffered_audio_byte_pos = self.audio_buffer[-1][0] + len(self.audio_buffer[-1][1])
                    else:
                        last_buffered_audio_byte_pos = playback_audio_byte_pos

                    desired_audio_ahead_bytes = PRE_BUFFER_SECONDS * AUDIO_SAMPLE_RATE * bytes_per_audio_frame

                    if (len(self.audio_buffer) < MAX_AUDIO_BUFFER_SIZE_CHUNKS and
                            (last_buffered_audio_byte_pos < playback_audio_byte_pos + desired_audio_ahead_bytes) and
                            last_buffered_audio_byte_pos < self.total_audio_bytes):

                        try:
                            # Read raw audio data from ffmpeg stdout
                            raw_data = self.audio_process.stdout.read(audio_chunk_bytes_size)
                            if raw_data:
                                # Store the starting byte offset for this chunk
                                # This offset is relative to the start of the audio stream
                                current_byte_offset = last_buffered_audio_byte_pos
                                self.audio_buffer.append((current_byte_offset, raw_data))
                            else:
                                # print("Buffering thread: No more audio data from ffmpeg stdout.")
                                pass  # ffmpeg process might still be running but has no more data
                        except ValueError:
                            # This can happen if stdout pipe is closed prematurely
                            # print("Buffering thread: ffmpeg stdout pipe closed.")
                            self.audio_process = None  # Mark as finished
                            pass
                        except Exception as e:
                            print(f"Buffering thread: Error reading audio from ffmpeg: {e}")
                            self.audio_process = None  # Mark as finished
                            pass
                elif self.audio_process and self.audio_process.poll() is not None:
                    # ffmpeg process has finished or crashed
                    if self.audio_process.returncode != 0:
                        print(
                            f"Buffering thread: ffmpeg process exited with error code {self.audio_process.returncode}")
                        print(self.audio_process.stderr.read().decode())
                    self.audio_process = None  # Mark as finished

                # --- Pruning old buffers ---
                # Prune video frames
                while len(self.frame_buffer) > 0 and \
                        self.frame_buffer[0][0] < playback_frame - (self.fps * POST_UNLOAD_SECONDS):
                    self.frame_buffer.popleft()

                # Prune audio chunks
                # Calculate how many bytes constitute POST_UNLOAD_SECONDS of audio
                bytes_to_unload = POST_UNLOAD_SECONDS * AUDIO_SAMPLE_RATE * bytes_per_audio_frame

                # Calculate the playback position in bytes
                playback_audio_byte_pos_for_pruning = int(
                    self.current_audio_ms / 1000 * AUDIO_SAMPLE_RATE * bytes_per_audio_frame)

                while len(self.audio_buffer) > 0 and \
                        self.audio_buffer[0][0] < playback_audio_byte_pos_for_pruning - bytes_to_unload:
                    self.audio_buffer.popleft()

            time.sleep(0.005)  # Reduced sleep for more active buffering

        cap.release()
        # Ensure ffmpeg process is terminated when buffering stops
        if self.audio_process:
            self.audio_process.kill()
            self.audio_process.wait()  # Wait for it to clean up
            self.audio_process = None
        print("Buffering thread: Exiting.")

    def _start_playback_timer(self):
        if self.playback_timer_id:
            GLib.source_remove(self.playback_timer_id)

        if self.fps > 0:
            frame_interval_ms = int(1000 / self.fps)
            self.playback_timer_id = GLib.timeout_add(frame_interval_ms, self._on_playback_timer)
            print(f"Video playback timer started at {self.fps} FPS ({frame_interval_ms}ms interval)")
        else:
            print("Cannot start video playback timer: FPS is 0.")

        # Start audio playback stream
        self._start_audio_stream()

    def _stop_playback_timer(self):
        if self.playback_timer_id:
            GLib.source_remove(self.playback_timer_id)
            self.playback_timer_id = None
            print("Video playback timer stopped.")

        self._pause_audio_stream()

    def _on_playback_timer(self):
        if not self.playback_running or not self.video_capture or not self.video_capture.isOpened():
            return False  # Stop the timer

        with self.buffer_lock:
            # --- Video Frame Processing ---
            if len(self.frame_buffer) > 0 and self.frame_buffer[0][0] == self.current_frame_number:
                frame_num_to_display, frame_data_to_display = self.frame_buffer.popleft()
                self._frame_for_drawing = frame_data_to_display
                self.video_area.queue_draw()  # Request redraw

                self.current_frame_number += 1
                self.update_timeline_and_label()

                # Check for end of video
                if self.current_frame_number >= self.total_frames:
                    print("Playback: End of video reached.")
                    self._stop_playback()
                    self.current_frame_number = self.total_frames
                    self.update_timeline_and_label()
                    return False  # Stop the timer

            else:
                # If frame is not at buffer front or buffer is empty for video
                if self.current_frame_number >= self.total_frames:
                    print("Playback: End of video already processed (at end).")
                    self._stop_playback()
                    return False

                # If the buffer has frames, but they are *ahead* of current_frame_number
                if len(self.frame_buffer) > 0 and self.frame_buffer[0][0] > self.current_frame_number:
                    print(
                        f"Video Playback: Current frame {self.current_frame_number} missed. Catching up to buffer at {self.frame_buffer[0][0]}.")
                    self.current_frame_number = self.frame_buffer[0][0]
                    self.video_area.queue_draw()
                    self.update_timeline_and_label()
                    return True  # Continue timer (will attempt to draw this frame next tick)

                # print(f"Video Playback: Waiting for frame {self.current_frame_number}. Buffer range: "
                #       f"{self.frame_buffer[0][0] if self.frame_buffer else 'N/A'}-"
                #       f"{self.frame_buffer[-1][0] if self.frame_buffer else 'N/A'}. Waiting for buffer...")
                return True  # Continue the timer, waiting for video frames

        return True  # Continue the timer (if video frame was displayed)

    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Callback function for sounddevice stream.
        outdata: NumPy array for audio data (fill this with your audio)
        frames: Number of frames (samples per channel) expected
        """
        if not self.playback_running:
            outdata.fill(0)  # Fill with silence if not playing
            return sd.CallbackFlags.CONTINUE  # Corrected: Uppercase CONTINUE

        bytes_per_audio_frame = AUDIO_CHANNELS * np.dtype(AUDIO_FORMAT).itemsize
        desired_bytes = frames * bytes_per_audio_frame

        # Using a byte counter to track current audio position more accurately
        # This will be updated by the actual amount of data pulled from buffer
        # self.current_audio_ms = self.get_current_time_s() * 1000 # Keep audio current with video master clock
        # No, the audio callback should *not* update current_audio_ms based on video time.
        # It should update current_audio_ms based on the actual audio it's playing.
        # The video time should eventually follow the audio time, or a separate sync mechanism is needed.
        # For now, let's just use a simple counter for audio position in the callback.
        # The main loop will update self.current_audio_ms when seeking, and the callback will adjust.

        data_to_play = b''
        with self.buffer_lock:
            # We want to find the chunk whose start_byte_offset is closest to (but not much before)
            # the current target playback position (self.current_audio_ms, converted to bytes).
            current_target_byte_pos = int(self.current_audio_ms / 1000 * AUDIO_SAMPLE_RATE * bytes_per_audio_frame)

            # Pop audio chunks that are already past the current video time, or too far behind to be relevant
            # Keep a small buffer of pre-loaded chunks at the front
            while self.audio_buffer and \
                    (self.audio_buffer[0][0] + len(self.audio_buffer[0][1]) < current_target_byte_pos - (
                            AUDIO_CHUNK_FRAMES * bytes_per_audio_frame * 2)):  # 2 chunks leeway
                self.audio_buffer.popleft()

            # Now, attempt to get data from the front of the buffer
            if self.audio_buffer:
                first_chunk_start_byte_pos, first_chunk_data = self.audio_buffer[0]

                # If the first chunk is significantly ahead of where we expect to be,
                # it means either current_audio_ms is very behind, or buffering is far ahead.
                # In such cases, we might need to skip some data or return silence.
                # For now, we prioritize playing available data, but be aware of sync issues.
                if first_chunk_start_byte_pos > current_target_byte_pos + (
                        AUDIO_CHUNK_FRAMES * bytes_per_audio_frame * 2):
                    # print(f"Audio callback: Buffer too far ahead. Expected {current_target_byte_pos} bytes, first chunk at {first_chunk_start_byte_pos}. Returning silence.")
                    outdata.fill(0)
                    return sd.CallbackFlags.CONTINUE

                # Take exactly 'desired_bytes' from the buffer
                if len(first_chunk_data) >= desired_bytes:
                    data_to_play = first_chunk_data[:desired_bytes]
                    self.audio_buffer[0] = (first_chunk_start_byte_pos + desired_bytes,
                                            first_chunk_data[desired_bytes:])
                else:
                    # Not enough data in the first chunk, take what's left and try next
                    data_to_play = first_chunk_data
                    self.audio_buffer.popleft()  # Remove the used chunk

                    # Try to fill remaining data from next chunks if available
                    remaining_bytes = desired_bytes - len(data_to_play)
                    while remaining_bytes > 0 and self.audio_buffer:
                        next_chunk_start_byte_pos, next_chunk_data = self.audio_buffer[0]
                        bytes_to_take = min(remaining_bytes, len(next_chunk_data))
                        data_to_play += next_chunk_data[:bytes_to_take]
                        self.audio_buffer[0] = (next_chunk_start_byte_pos + bytes_to_take,
                                                next_chunk_data[bytes_to_take:])
                        remaining_bytes -= bytes_to_take
                        if not self.audio_buffer[0][1]:  # If chunk is fully consumed
                            self.audio_buffer.popleft()

            # If not enough data was accumulated, pad with silence
            if len(data_to_play) < desired_bytes:
                data_to_play += b'\x00' * (desired_bytes - len(data_to_play))
                # print(f"Audio Playback: Buffer underrun. Expected {desired_bytes} bytes, got {len(data_to_play)}. Padding with silence.")

        # Convert raw bytes to NumPy array and copy to outdata
        outdata[:] = np.frombuffer(data_to_play, dtype=AUDIO_FORMAT).reshape(-1, AUDIO_CHANNELS)

        # Update current_audio_ms based on *actual* frames played
        # This is important for tracking current audio position.
        self.current_audio_ms += (frames / AUDIO_SAMPLE_RATE) * 1000

        return sd.CallbackFlags.CONTINUE  # Corrected: Uppercase CONTINUE

    def _start_audio_stream(self):
        if self.audio_process and not self.audio_stream:
            try:
                self.audio_stream = sd.OutputStream(
                    samplerate=AUDIO_SAMPLE_RATE,
                    channels=AUDIO_CHANNELS,
                    dtype=AUDIO_FORMAT,
                    blocksize=AUDIO_CHUNK_FRAMES,  # This defines 'frames' in callback
                    callback=self._audio_callback
                )
                self.audio_stream.start()
                print("Audio stream started (SoundDevice).")
            except Exception as e:
                print(f"ERROR: Could not start audio stream (SoundDevice): {e}")
                self.audio_stream = None

    def _pause_audio_stream(self):
        if self.audio_stream and self.audio_stream.active:  # Corrected: .active
            self.audio_stream.stop()
            print("Audio stream paused (SoundDevice).")

    def _close_audio_stream(self):
        if self.audio_stream:
            if self.audio_stream.active:  # Corrected: .active
                self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            print("Audio stream closed (SoundDevice).")

        # Ensure ffmpeg process is also terminated if open
        if self.audio_process:
            self.audio_process.kill()
            self.audio_process.wait()
            self.audio_process = None

    def on_play_pause_clicked(self, widget):
        if not self.video_capture or not self.video_capture.isOpened():
            print("No video loaded.")
            return

        if self.playback_running:
            print("Pausing video...")
            self.playback_running = False
            self._stop_playback_timer()  # This also pauses audio
            self.play_pause_button.set_label("▶ Play")
            self.video_area.queue_draw()
        else:
            print("Playing video...")
            self.playback_running = True
            self.play_pause_button.set_label("⏸ Pause")
            self._start_playback_timer()  # This also starts audio
            self.update_timeline_and_label()

    def on_timeline_changed(self, scale):
        pass  # Only seek on button release

    def on_timeline_released(self, scale, event):
        if not self.video_capture or not self.video_capture.isOpened():
            return

        seek_percent = scale.get_value()
        target_time_s = (seek_percent / 100.0) * self.video_duration_s
        target_frame = int(target_time_s * self.fps)
        target_audio_ms = int(target_time_s * 1000)

        print(f"Seeking to {seek_percent:.2f}% (video frame {target_frame}, audio {target_audio_ms}ms)")

        # Call the encapsulated seek logic
        self._perform_seek(target_frame, target_audio_ms)

    def on_key_press(self, widget, event):
        if not self.video_capture or not self.video_capture.isOpened():
            return False

        if event.keyval == Gdk.KEY_space:
            self.on_play_pause_clicked(None)
            return True

        current_time_s = self.get_current_time_s()
        target_time_s = current_time_s

        if event.keyval == Gdk.KEY_Left:
            target_time_s = max(0, current_time_s - 5)  # Skip backward by 5s
            print(f"Skip backward to {target_time_s:.2f}s")
        elif event.keyval == Gdk.KEY_Right:
            target_time_s = min(self.video_duration_s, current_time_s + 5)  # Skip forward by 5s
            print(f"Skip forward to {target_time_s:.2f}s")
        else:
            return False  # Not our key

        target_frame = int(target_time_s * self.fps)
        target_audio_ms = int(target_time_s * 1000)

        # Update timeline scale visually first (optional, but good for UX)
        new_seek_percent = (target_time_s / self.video_duration_s) * 100 if self.video_duration_s > 0 else 0
        self.timeline_scale.handler_block(self.timeline_scale_handler_id)
        self.timeline_scale.set_value(new_seek_percent)
        self.timeline_scale.handler_unblock(self.timeline_scale_handler_id)

        # Call the encapsulated seek logic
        self._perform_seek(target_frame, target_audio_ms)

        return True

    def _perform_seek(self, target_frame, target_audio_ms):
        """Helper function to encapsulate seeking logic."""
        was_playing = self.playback_running
        self._stop_playback()
        self._stop_buffering()  # This kills existing ffmpeg process and releases video_capture
        self._close_audio_stream()  # Ensure audio stream is closed (and ffmpeg killed)

        with self.buffer_lock:
            self.frame_buffer.clear()
            self.audio_buffer.clear()
            self._frame_for_drawing = None

        # Set new current positions
        self.current_frame_number = target_frame
        self.current_audio_ms = target_audio_ms

        # Re-initialize video capture for seek
        self.video_capture = cv2.VideoCapture(self.current_filepath)
        if not self.video_capture.isOpened():
            print(f"ERROR: Could not re-open video file for seeking: {self.current_filepath}")
            return
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        # Re-initialize ffmpeg audio process with seek
        if self.current_filepath and self.total_audio_ms > 0:
            try:
                ffmpeg_args = {
                    'format': 's16le',
                    'acodec': 'pcm_s16le',
                    'ac': AUDIO_CHANNELS,
                    'ar': AUDIO_SAMPLE_RATE
                }
                # Use -ss flag for seeking
                self.audio_process = (
                    ffmpeg
                    .input(self.current_filepath, ss=target_audio_ms / 1000.0)  # Seek using seconds
                    .output('pipe:', **ffmpeg_args)
                    .run_async(pipe_stdout=True)
                )
                print(f"FFmpeg audio extraction process re-started for seek to {target_audio_ms / 1000.0:.2f}s.")
            except Error as e:  # Use the imported Error
                print(f"FFmpeg Error during seek: {e.stderr.decode()}")
                self.audio_process = None
            except Exception as e:
                print(f"ERROR: Could not restart audio stream with ffmpeg for seek: {e}")
                self.audio_process = None
        else:
            self.audio_process = None

        # Restart buffering from the new position
        self.buffering_running = True
        self.buffering_thread = threading.Thread(target=self._media_buffering_thread, args=(self.current_filepath,))
        self.buffering_thread.daemon = True
        self.buffering_thread.start()

        # Give buffering thread a moment to fill some initial data
        time.sleep(0.2)  # Give buffer a moment to refill after seek

        # Update UI immediately after seek
        self.video_area.queue_draw()
        self.update_timeline_and_label()

        if was_playing:
            self.on_play_pause_clicked(None)

    def get_current_time_s(self):
        # Prefer video time as the master
        if self.fps > 0:
            return self.current_frame_number / self.fps
        return 0

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_timeline_and_label(self):
        current_s = self.get_current_time_s()
        total_s = self.video_duration_s

        if total_s > 0:
            new_value = (current_s / total_s) * 100
            self.timeline_scale.handler_block(self.timeline_scale_handler_id)
            self.timeline_scale.set_value(new_value)
            self.timeline_scale.handler_unblock(self.timeline_scale_handler_id)

            self.time_label.set_label(f"{self.format_time(current_s)} / {self.format_time(total_s)}")
        else:
            self.timeline_scale.set_value(0)
            self.time_label.set_label("00:00 / 00:00")

        return True  # Continue timeout if scheduled (if this is called by a timer)

    def _stop_playback(self):
        self.playback_running = False
        self._stop_playback_timer()  # This also pauses audio
        self.play_pause_button.set_label("▶ Play")
        with self.buffer_lock:
            self._frame_for_drawing = None
        self.video_area.queue_draw()

    def _stop_buffering(self):
        self.buffering_running = False
        if self.buffering_thread and self.buffering_thread.is_alive():
            print("Stopping buffering thread...")
            self.buffering_thread.join(timeout=2.0)
            if self.buffering_thread.is_alive():
                print("Warning: Buffering thread did not terminate cleanly after 2 seconds.")

        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        # Ensure ffmpeg process is also terminated when buffering stops
        if self.audio_process:
            self.audio_process.kill()
            self.audio_process.wait()
            self.audio_process = None

        with self.buffer_lock:
            self.frame_buffer.clear()
            self.audio_buffer.clear()

    def on_destroy(self, widget):
        print("Application destroying. Stopping threads and releasing resources.")
        self._stop_playback()
        self._stop_buffering()
        self._close_audio_stream()

        Gtk.main_quit()


if __name__ == "__main__":
    win = VideoPlayer()
    win.show_all()
    Gtk.main()
