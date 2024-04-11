import sys, os, logging, cv2, json, threading, sqlite3
from datetime import datetime
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from notif_ui.success_window import Ui_success_win
from notif_ui.failed_window import Ui_failed_win
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip

from .sampleplayer import Ui_videoplayer # change to "from sampleplayer import Ui_videoplayer if running directly"


MAIN_PATH = os.getcwd()
SAVED_VIDEO_CLIPS_PATH = os.path.join(MAIN_PATH, 'saved_clips')
### Prevents multithreading process to avoid conflict in resources
lock = threading.Lock()

db=sqlite3.connect('cctvapp.db')
cursor=db.cursor()

# Create the user_logs_directory folder if it doesn't exist
log_directory = "user_logs_directory"
os.makedirs(log_directory, exist_ok=True)

# JSON file path
json_file_path = os.path.join(log_directory, 'user_logs.json')

# Configure the logging module
logging.basicConfig(level=logging.INFO,
                    format='%(message)s')

# Function to log user activities
def log_activity(username, activity, status, log_level=logging.INFO):
    timestamp = datetime.now().strftime('%b %d, %Y - %H:%M:%S')
    
    # Read existing JSON data from the file if it exists
    existing_data = {}
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            try:
                existing_data = json.load(json_file)
            except json.JSONDecodeError:
                pass

    # Create a log entry dictionary
    log_entry = {
        "timestamp": timestamp,
        "activity": activity,
        "status": status
    }

    # check if the username is in the DB
    cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (username,))
    check_logusername = cursor.fetchone()

    if check_logusername:
        # Check if the username already exists in the data
        if username in existing_data:
            existing_data[username].append(log_entry)
        else:
            # If the username doesn't exist, create a new entry for it
            existing_data[username] = [log_entry]

    # Save the updated data back to the JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

    # Check the log level and log accordingly
    if log_level == logging.INFO:
        logging.info(log_entry)

class VideoPlayer(QMainWindow, Ui_videoplayer):
    def __init__(self, video_filepath, position_seconds, get_userame, duration, export_path, input_filter_dict, timestamps_in_seconds_to_overlay=None):
        super().__init__()
        self.ui = Ui_videoplayer()
        self.setupUi(self)
        self.center()

        self.passusername = get_userame

        self.video_filepath = video_filepath
        self.position_seconds = position_seconds
        self.timestamps_in_seconds_to_overlay = timestamps_in_seconds_to_overlay
        self.video_started = False # Indicator if the video player has already started playing for the first time. Initialize to False
        self.savebutton.setVisible(False)

        self.input_filter_dict = input_filter_dict # Attribute for input_filter_dict used for providing information for the first column of saved_table in On_Progress.py

        # cap = cv2.VideoCapture(self.video_filepath) # Capture the video
        # total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # Get number of frames in the video
        # fps = int(cap.get(cv2.CAP_PROP_FPS)) # Get fps
        # self.input_video_duration = total_frames / fps # Calculate duration
        self.input_video_duration = duration
        self.export_path = export_path
        # print(self.export_path)

        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.videoscreen)
        self.media_player.setSource(QUrl.fromLocalFile(rf"{self.video_filepath}"))
        

        self.slider = self.videotimebar
        self.add_slider_bar_timestamp_overlays()
        self.slider.video_duration = self.input_video_duration
        self.slider.timestamps_in_seconds_to_overlay = self.timestamps_in_seconds_to_overlay
        self.slider.setRange(0, 0)  # Set the initial range to 0 (will be updated later)
        self.slider.sliderPressed.connect(self.pauseplay_video)
        self.slider.sliderReleased.connect(self.pauseplay_video)


        # Connect the slider's valueChanged signal to set_position
        self.slider.valueChanged.connect(self.set_position)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_slider_position)
        self.update_timer.start()

        self.timer_label = self.videotime
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_display)
        self.timer.start()

        self.timer_labelleft = self.videotimeleft
        self.timerleft = QTimer(self)
        self.timerleft.timeout.connect(self.update_timer_left)
        self.timerleft.start()

        self.pause_button = self.playbutton
        self.pause_button.clicked.connect(self.pauseplay_video)

        self.clip_button = self.clipbutton
        self.clip_button.clicked.connect(self.clip_video)

        self.savebutton.clicked.connect(self.save_video_clip)

        # Store the original slider handle (thumb) stylesheet
        self.original_thumb_stylesheet = self.slider.styleSheet()

        # Connect the durationChanged signal to update the slider range
        self.media_player.durationChanged.connect(self.update_slider_range)

        # print(timestamps_in_seconds_to_overlay)

    
    def add_slider_bar_timestamp_overlays(self):
        if self.timestamps_in_seconds_to_overlay:
            self.slider.class_timestamps = self.timestamps_in_seconds_to_overlay


    def update_slider_range(self, duration):
        # Update the slider's maximum value based on the video duration
        if duration > 0:
            self.slider.setRange(0, duration // 1000)  # Convert to seconds
        else:
            self.slider.setRange(0, 0)
        

    def pauseplay_video(self):
        if self.pause_button.text() == "PLAY":
            # If it is the first time playing the video, start to the chosen/double-clicked timestamp
            if not self.video_started:
                # print(self.position_seconds)
                self.set_position(self.position_seconds)
                self.video_started = True # Make the indicator True because it was already played for the first time
            self.pause_button.setText("PAUSE")
            self.media_player.play()
        else:
            self.pause_button.setText("PLAY")
            self.media_player.pause()

    # To toggle show/hide the clipping knobs and save button
    # To change the text of self.clip_button as well
    def clip_video(self):
        if os.path.exists(self.export_path):
            self.toggle_clip_button()
        else:
            os.makedirs(self.export_path, exist_ok=True)
            self.toggle_clip_button()
    
    def toggle_clip_button(self):
            if self.clip_button.text() == "START CLIPPING":
                self.clip_button.setText("END CLIPPING")
                self.savebutton.setVisible(True)
                self.slider.toggle_clipping_knobs_visibility(True)
                logname = self.passusername
                activity = "Initiated the video clipping feature."
                logstatus = "NORMAL"
                log_activity(logname, activity, logstatus)
                # Commented out just in case
                # Change the slider handle (thumb) color to red
                # self.slider.setStyleSheet("QSlider::handle:horizontal { background-color: red; }")
            else:
                self.clip_button.setText("START CLIPPING")
                self.savebutton.setVisible(False)
                self.slider.toggle_clipping_knobs_visibility(False)
                logname = self.passusername
                activity = "Closed the video clipping feature."
                logstatus = "NORMAL"
                log_activity(logname, activity, logstatus)
                # Commented out just in case
                # Revert the slider handle (thumb) color to the original style
                # self.slider.setStyleSheet(self.original_thumb_stylesheet)
        
    def save_video_clip(self):
        logname = self.passusername
        activity = "Successfully clipped a portion of the video."
        logstatus = "SUCCESS"
        log_activity(logname, activity, logstatus)

        timestamp_clip_start = map_value_to_range(self.slider.trim_start_knob_pos_percent, 0, 1, 0, self.input_video_duration) # Get the current position of the start knob (refer to CustomSlider class in sampleplayer.py) and convert it to a value from 0 to the duration of the video in seconds
        timestamp_clip_end = map_value_to_range(self.slider.trim_end_knob_pos_percent, 0, 1, 0, self.input_video_duration) # Do the same for the end timestamp of the clip
        # print(timestamp_clip_start, timestamp_clip_end, self.slider.trim_start_knob_pos_percent, self.slider.trim_end_knob_pos_percent)
        # os.makedirs(self.export_path, exist_ok=True) # Create self.export_path if it does not exist
        current_datetime_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') # String formatted of current datetime
        filenameclip = f'saved_clip_{current_datetime_str}.mp4'
        destination_filepath = os.path.join(self.export_path, f'saved_clip_{current_datetime_str}.mp4') # Specified filepath
        ffmpeg_extract_subclip(self.video_filepath, timestamp_clip_start, timestamp_clip_end, destination_filepath) # Clip and save the video to the specified filepath
        print(f"Clip saved to {destination_filepath} successfully saved") # Indicator if it was successfully saved
        with lock:
            print("TIME DIFF:")
            print(timestamp_clip_start, timestamp_clip_end, timestamp_clip_start-timestamp_clip_end)

            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%b %d, %Y - %H:%M:%S")

            clip = VideoFileClip(destination_filepath)
            vidduration = clip.duration
            vidduration_str = str(int(vidduration))
            clip.close()

            savedclips_directory = "saved_videos"
            os.makedirs(savedclips_directory, exist_ok=True)
            self.clips_file_path = os.path.join(savedclips_directory, 'savedclips.json')
            user_clips = self.passusername
            self.clipped = {}  # Initialize clip

            if os.path.exists(self.clips_file_path):
                with open(self.clips_file_path, 'r') as file:
                    self.clipped = json.load(file)

            # Check if user_clips is present
            if user_clips not in self.clipped:
                # User is not present, create a new entry
                self.clipped[user_clips] = []

            # Append new data to the user_clips entry
            new_entry = {
                'input_filter_dict' : self.input_filter_dict,
                'filename': filenameclip,
                'timestamp': formatted_datetime,
                'duration': vidduration_str,
                'path': self.export_path
            }

            self.clipped[user_clips].append(new_entry)

            # Save the updated data back to the file
            with open(self.clips_file_path, 'w') as file:
                json.dump(self.clipped, file, indent=2)

            self.open_successreset_ui = clip_success()
            self.open_successreset_ui.show()



    def set_position(self, position):
        position_ms = (position) * 1000
        self.media_player.setPosition(position_ms)

    def update_slider_position(self):
        # Update the slider's value based on the current position
        position = self.media_player.position()
        # print(position / 1000)
        self.slider.setValue(position // 1000)  # Convert to seconds

    def update_timer_display(self):
        # Get the current playback position
        position = self.media_player.position()
        # Format the position as a time string (e.g., "00:00")
        position_str = QTime.fromMSecsSinceStartOfDay(position).toString("mm:ss")
        # Update the timer label with the formatted string (running time)
        self.timer_label.setText(position_str)

    def update_timer_left(self):
        # Get the current playback position and duration
        position = self.media_player.position()
        duration = self.media_player.duration()

        # Calculate the remaining time
        remaining_time_ms = duration - position
        # Format the remaining time as a time string (e.g., "00:00")
        remaining_time_str = QTime.fromMSecsSinceStartOfDay(remaining_time_ms).toString("-mm:ss")
        # Update the timer label with the formatted string (remaining time)
        self.timer_labelleft.setText(remaining_time_str)

    def center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2 - 35
        self.move(x, y)

class clip_success(QMainWindow, Ui_success_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black; }")
        current_success_text =  self.tofillupsuccess
        current_success_text.setText(' Clipping complete.\n\n Successfully clipped your selected range.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_backvideo)

    def ok_backvideo(self):
        self.close()

# Helper function to convert values from a range of values to another range
# This will be used to convert the current position of start and end knob (0.0 - 1.0) to 0.0 to whatever the duration of the input video
def map_value_to_range(value, from_min, from_max, to_min, to_max):
    # Calculate the percentage of 'value' in the original range
    percentage = (value - from_min) / (from_max - from_min)

    # Map the percentage to the new range
    mapped_value = to_min + percentage * (to_max - to_min)

    # Ensure the mapped value stays within the target range
    return max(to_min, min(mapped_value, to_max))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoPlayer()
    window.show()
    sys.exit(app.exec())