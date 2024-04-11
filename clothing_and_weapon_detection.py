# Import dependencies
# import torch
import os
import shutil
import time
import glob
import json
import pytz
from win32com.propsys import propsys, pscon

from datetime import datetime
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip

import yolov5.detect_clothings as dtc # detect_clothings.py from yolov5 folder
import yolov5.detect_weapon as dtw # detect_weapon.py from yolov5 folder


# Clothings class mapping - needed to create a reversed clothings class mapping 
clothings_class_mapping = {
    'sleeved_shirt' : 0,
    'sleeveless_top' : 1,
    'outwear' : 2,
    'shorts' : 3,
    'trousers' : 4,
    'skirt' : 5,
    'dress' : 6
}

reversed_clothings_class_mapping = dict([(val, key) for key, val in clothings_class_mapping.items()])


# #============== ABOSULTE FILEPATHS ========================#
# # WEAPON-RELATED PATHS/FILEPATHS
# WEAPON_OD_FILEPATH = r'D:\pd2_app\od_models\weapon_od.pt' # Change accordingly 
# WEAPON_VIDEO_WITH_BBOXES_SAVE_PATH = r'D:\pd2_app\output_videos_with_weapons\exp'
# WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH = r'D:\pd2_app\file_weapons.txt'


# # CLOTHING-RELATED PATHS/FILEPATHS
# CLOTHINGS_OD_FILEPATH = r'D:\pd2_app\od_models\clothings_od.pt'
# CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH = r'D:\pd2_app\file_clothings.txt'


# WEAPONS_OUTPUT_VIDEOS_FROM_YOLOV5 = r'D:\pd2_app\output_videos_with_weapons' # Change accordingly
# CLOTHINGS_OUTPUT_VIDEOS_FROM_YOLOV5 = r'D:\pd2_app\output_videos_with_clothings_and_weapons' # Change accordingly
# OUTPUT_VIDEO_FILENAME = 'output'
# OUTPUT_VIDEO_PATH = r'D:\pd2_app\output_videos_final' # Change accordingly


#================RELATIVE PATHS====================#
"""
With these paths, the main driver code can be ran directly without changing these paths
depending on the organization of your unit's directory 
"""
MAIN_PATH = os.getcwd()
TEMP_PATH = os.path.join(MAIN_PATH, 'temp')
TEMP_OUTPUT_PATH = os.path.join(MAIN_PATH, 'temp_output')
TABLE_DATA_JSON_PATH = os.path.join(TEMP_OUTPUT_PATH, 'table_data.json')

# WEAPON-RELATED PATHS/FILEPATHS
WEAPON_OD_FILEPATH = os.path.join(MAIN_PATH, 'od_models/weapon_od.pt')
WEAPON_VIDEO_WITH_BBOXES_SAVE_PATH = os.path.join(TEMP_PATH, 'output_videos_with_weapons', 'exp')
WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH = os.path.join(TEMP_PATH, 'file_weapons.txt')


# CLOTHING-RELATED PATHS/FILEPATHS
CLOTHINGS_OD_FILEPATH = os.path.join(MAIN_PATH, 'od_models/clothings_od.pt')
CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH = os.path.join(TEMP_PATH, 'file_clothings.txt')


WEAPONS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH = os.path.join(TEMP_PATH, 'output_videos_with_weapons')
CLOTHINGS_ONLY_OUTPUT_VIDEOS_FROM_YOLOV5_PATH = os.path.join(TEMP_PATH, 'output_videos_with_clothings')
CLOTHINGS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH = os.path.join(TEMP_PATH, 'output_videos_with_clothings_and_weapons')
OUTPUT_VIDEO_FILENAME = 'output'
OUTPUT_VIDEO_PATH = os.path.join(MAIN_PATH, 'output_videos_final')


USER_APP_SETTING_PATH = os.path.join(MAIN_PATH, 'app_settings', 'application_settings.config')


"""
Description: 
    Detects clothing and their colors. 
    It also provides the corresponding timestamp in HH:MM:SS and second format in a text file.
    It mainly uses detect.py from YOLOv5 that was modified according to purpose.
Parameters:
    input_video_filepath: string (required)
    conf_thresh: float (0.0 to 1.0 - optional), 0.5 by default
    classes: list
Output:
    None
"""
def detect_clothings_and_colors_from_video_and_get_reference_frame_timestamps(input_video_filepath, clothings_to_detect_and_colors, conf_thresh=0.5, *classes, cleanup_data, progress_data, unix_timestamp_datetime_created=None, is_frame_in_nightvision_list=None, project=CLOTHINGS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH, is_clothings_only=True):
    os.makedirs(project, exist_ok=True)
    print(f'CLASSES: {classes}')
    dtc.run(
        weights = CLOTHINGS_OD_FILEPATH,
        source = input_video_filepath,
        conf_thres = conf_thresh,
        project = project,
        classes = classes,
        save_colors_and_timestamps=False,
        line_thickness=1,
        clothings_to_detect_and_colors=clothings_to_detect_and_colors,
        cleanup_data=cleanup_data,
        progress_data=progress_data, # For progress bar
        unix_timestamp_datetime_created=unix_timestamp_datetime_created, # To keep track of when the file was created,
        is_frame_in_nightvision_list=is_frame_in_nightvision_list,
        is_clothing_only=is_clothings_only
    )


"""
Description: 
    Detects weapons and write their corresponding timestamps in a text file
    It mainly uses detect.py from YOLOv5 that was modified according to purpose.
Parameters:
    input_video_filepath: string (required)
    conf_thresh: float (0.0 to 1.0 - optional), 0.5 by default
    classes: list
Output:
    None
"""
def detect_weapon_from_video_and_get_reference_frame_timestamps(input_video_filepath, conf_thresh=0.5, *classes, cleanup_data, progress_data, is_weapon_only=True):
    os.makedirs(WEAPONS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH, exist_ok=True)
    if None in classes:
        is_frame_in_nightvision_list = dtw.run(
            weights = WEAPON_OD_FILEPATH,
            source = input_video_filepath,
            conf_thres = conf_thresh,
            project = WEAPONS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH,
            classes = None,
            save_timestamps = True,
            line_thickness = 1,
            progress_data = progress_data,
            is_weapon_only = is_weapon_only,
            cleanup_data = cleanup_data
        )

        return is_frame_in_nightvision_list
    else:
        is_frame_in_nightvision_list = dtw.run(
            weights = WEAPON_OD_FILEPATH,
            source = input_video_filepath,
            conf_thres = conf_thresh,
            project = WEAPONS_OUTPUT_VIDEOS_FROM_YOLOV5_PATH,
            classes = classes,
            save_timestamps=True,
            line_thickness=1,
            progress_data = progress_data,
            is_weapon_only = is_weapon_only,
            cleanup_data = cleanup_data
        )

        return is_frame_in_nightvision_list


"""
Description: 
    - Reads the temporarily saved 'file_clothings.txt' that contains the 
    clothing, colors, timestamps in HH:MM:SS and seconds format and return the content.
    - This can be used to get the contents to display in the filtering summary table in GUI
    - Note: 'file_clothings.txt' is created by detect_clothings.py during its detection process
Parameters:
    None
Output:
    list of lists
"""
def get_clothings_with_their_colors_timestamps_from_text_file():
    try:
        clothings_colors_and_timestamps = []
        with open(CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'r') as f:
            for line in f:
                tuple_data_clothings_colors_and_timestamps = eval(line.strip())
                clothings_colors_and_timestamps.append(list(tuple_data_clothings_colors_and_timestamps))
        
        return clothings_colors_and_timestamps
    except:
        print(f"{CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH} not removed. There was no clothings detected.")
        return []


"""
Description: 
    - Reads the temporarily saved 'file_clothings.txt' that contains the 
    clothing, colors, timestamps in HH:MM:SS and seconds format and return the content.
    - This can be used to get the contents to display in the filtering summary table in GUI
    - Note: 'file_clothings.txt' is created by detect_clothings.py during its detection process
Parameters:
    None
Output:
    list of lists
"""
def get_weapons_with_their_timestamps_from_text_file():
    try:
        weapons_and_timestamps = []
        with open(WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'r') as f:
            for line in f:
                tuple_data_weapon_and_timestamp = eval(line.strip())
                weapons_and_timestamps.append(list(tuple_data_weapon_and_timestamp))

        return weapons_and_timestamps
    except:
        print(f"{WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH} not opened and removed. There were no weapons detected.")
        return []


# def get_clothing_unique_timestamps_from_text_file():
#     unique_timestamps_in_seconds = set()

#     with open(CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'r') as f:
#         for line in f:
#             timestamp_in_seconds = line.strip().split(',')[-1].strip(')')
#             unique_timestamps_in_seconds.add(int(timestamp_in_seconds))
    
#     return list(unique_timestamps_in_seconds)


# def get_weapon_unique_timestamps_from_text_file():
#     unique_timestamps_in_seconds = set()

#     with open(WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'r') as f:
#         for line in f:
#             timestamp_in_seconds = line.strip().split(',')[-1].strip(')')
#             unique_timestamps_in_seconds.add(int(timestamp_in_seconds))
    
#     return list(unique_timestamps_in_seconds)


# def get_video_fps(input_video_filepath):
#     video_clip = VideoFileClip(input_video_filepath)
#     fps = video_clip.fps
#     video_clip.reader.close()
#     return fps

# # Convert seconds to HH-MM-SS
# def seconds_to_timestamp(seconds):
#     hours = seconds // 3600
#     minutes = (seconds % 3600) // 60
#     seconds_remain = seconds % 60
#     return f"{int(hours):02d}-{int(minutes):02d}-{int(seconds_remain):02d}"

# def get_seconds_from_timestamp(timestamp):
#     dt_obj = datetime.strptime(timestamp, '%H:%M:%S')
#     seconds = dt_obj.hour * 3600 + dt_obj.minute * 60 + dt_obj.second
#     return seconds


# def get_video_duration(input_video_filepath):
#     video_capture = VideoFileClip(input_video_filepath)
#     duration = video_capture.duration
#     video_capture.reader.close()
#     return duration


# Only for printing strings inside a box or rectangle
def print_msg_box(msg, indent=1, width=None, title=None):
    """Print message-box with optional title."""
    lines = msg.split('\n')
    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'╔{"═" * (width + indent * 2)}╗\n'  # upper_border
    if title:
        box += f'║{space}{title:<{width}}{space}║\n'  # title
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
    box += ''.join([f'║{space}{line:<{width}}{space}║\n' for line in lines])
    box += f'╚{"═" * (width + indent * 2)}╝'  # lower_border
    print(box)


# Deletes a folder, directory, or path
def delete_folder(path):
    try:
        shutil.rmtree(path)
    except Exception as error:
        print(f"Error in deleting temp folder path:{path}.\nError: {error}")


"""
Description: 
    - Extracts timestamps from text file and maps them to a specific category
    - By mapping, meaning it assigns which timestamps (unix format) the weapons or clothings were found
Parameters:
    text_file_path: string path (required)
    content: string (required)
Output:
    Dictionary (dict) of timestamps
"""
def extract_timestamps_from_text_file(text_file_path, content):
    try:
        timestamps_dict = {} # Empty dictionary
        
        with open(text_file_path, 'r') as file: # Read text file
            for line in file: # Iterate through each line
                if content == 'clothings': # If clothings
                    formatted_line = eval(line) 
                    item = formatted_line[0][1] # Get the name of the clothing class
                    timestamp = formatted_line[1] # Get the timestamp

                    if item not in timestamps_dict: # Add a new key with empty set as the value if non-existent
                        timestamps_dict[item] = set()
                    
                    timestamps_dict[item].add(timestamp) # Add the timestamp to the set of the clothing class being iterated. Using a set avoids duplication

                elif content == 'weapons':  # If weapons
                    formatted_line = eval(line) 
                    item = formatted_line[0]    # Get the name of the weapon class
                    timestamp = formatted_line[1] # Get the timestamp

                    if item not in timestamps_dict: # Add a new key with empty set as the value if non-existent
                        timestamps_dict[item] = set()
                    
                    timestamps_dict[item].add(timestamp) # Add the timestamp to the set of the weapon class being iterated. Using a set avoids duplication


        return timestamps_dict # Return the dictionary
    
    except Exception as e: # Catches error by displaying error message on the terminal.
        print(e)
        print(f"No {content} found in the video.")
        return {}


def get_unique_and_common_timestamps(clothings_timestamps, weapons_timestamps):
    # print(f"CLOTHING TIMESTAMPS: {clothings_timestamps}")
    # print(f"WEAPON TIMESTAMPS: {weapons_timestamps}")
    try:
        combined_clothings_and_weapons_timestamps = {**weapons_timestamps, **clothings_timestamps}
        unique_and_common_timestamps = set.union(*combined_clothings_and_weapons_timestamps.values())
        return sorted(list(unique_and_common_timestamps))
    except:
        print("There were no either weapons or clothings detected.")
        return []


# def create_main_path():
#     os.makedirs(MAIN_PATH, exist_ok=True)

# def remove_output_videos_final_dir():
#     if os.path.exists(OUTPUT_VIDEO_PATH):
#         shutil.rmtree(OUTPUT_VIDEO_PATH)


# def convert_timestamp_to_datetime(timestamp):
#     return datetime.strptime(timestamp, '%H:%M:%S').time()


def main_driver_code(input_video_filepaths, weapons_to_detect, clothings_to_detect_and_colors, username, input_filter_dict, progress_callback=None, cancel_callback=None):
    total_time = 0 # To measure the total time elapsed to process all the frames in all videos
    progress_bar_value_indices = range(0, len(input_video_filepaths)*2, 2) # Keeps track of the indices to set the minimum and maximum value of the progress bar
    
    table_data_for_all_videos = {} # dictionary that will contain table data for each video for a specific username and start-end datetime of processing

    start_detection_datetime = datetime.now() # Keep track of the detection process' start datetime

    # Iterate through each input video filepath
    print(f"Datetime-filtered videos: {input_video_filepaths}")
    for idx, input_video_filepath in zip(progress_bar_value_indices, input_video_filepaths):
        # import cv2
        # print(f"FPS Weapon Detection.py: {cv2.VideoCapture(input_video_filepath).get(cv2.CAP_PROP_FPS)}")
        print(f"Processing: {input_video_filepath}")

        # For each detection, the contents of TEMP_PATH is recreated to delete the past detection
        if os.path.exists(TEMP_PATH): # Delete TEMP_PATH if it exists
            delete_folder(TEMP_PATH)
        os.makedirs(TEMP_OUTPUT_PATH, exist_ok=True) # Recreate the TEMP_PATH

        # Parse the passed clothings_to_detect_and_colors dictionary then get the list of clothings
        list_of_clothings_to_detect = [clothings_class_mapping[i] for i in (clothings_to_detect_and_colors.keys()) if i != 'none']

        # Get the "media created" attribute of the video file
        try:
            properties = propsys.SHGetPropertyStoreFromParsingName(input_video_filepath.replace('/', '\\'))
            dt_property = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
            unix_timestamp_datetime_created = dt_property.timestamp()
        except Exception as error:
            print(f"Error: {error}")

        # Create a dictionary data to store all the data needed to update the progress bar
        progress_data = {
            'num_of_input_video_filepaths' : len(input_video_filepaths),
            'zero_indexed_nth_video_filepath' : idx,
            'progress_callback' : progress_callback,
            'cancel_callback' : cancel_callback
        }

        if (weapons_to_detect != ['None']) and (list_of_clothings_to_detect == []): # Executed when only a weapon is the only object selected (no clothings) #############################################################################
            print('FIRST CONDITIONAL MAIN DRIVER CODE - WEAPON ONLY')
            # Detect weapon in video
            start_time = time.time()

            cleanup_data = {
                'username' : username,
                'start_detection_datetime' : start_detection_datetime
            }

            is_frame_in_nightvision_list = detect_weapon_from_video_and_get_reference_frame_timestamps(input_video_filepath, 0.5, *weapons_to_detect, cleanup_data=cleanup_data, progress_data=progress_data)
            end_time = time.time()
            print_msg_box(f"detect_weapon_from_video_and_get_reference_frame_timestamps() -> Elapsed Time: {round(end_time - start_time, 2)}")
            total_time += round(end_time - start_time, 2)

            weapons_timestamps = extract_timestamps_from_text_file(WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'weapons')
            weapons_data = get_weapons_with_their_timestamps_from_text_file()

            table_data = {} # Create empty dictionary to contain table data for a specific video

            # Return weapons_timestamps (empty dictionary will be returned if this condition is met) if there are no detected weapons
            if len(weapons_timestamps) <= 0:
                return clothings_timestamps
            else:
                for timestamp in sorted(list(set.union(*weapons_timestamps.values()))): # Iterate through each unique and common timestamps
                    # Structure the table_data dictionary such that:
                    # table_data : {
                    #   timestamp : {
                    #       'weapons' : [],
                    #       'clothing_and_colors' : []
                    #   },
                    #   ...
                    # }
                    table_data[str(timestamp)] = {'weapons': [], 'clothing_and_colors': []}


                for weapon_timestamp_item in weapons_data: # Iterate through each timestamp in weapons_data
                    weapon_timestamp = str(weapon_timestamp_item[1]) # Get the timestamp
                    table_data[weapon_timestamp]['weapons'].append(weapon_timestamp_item) # Append the [weapon, timestamp] element to the corresponding list value of timestamp key

                table_data_for_all_videos[input_video_filepath] = table_data

                # Keep track of the detection process end datetime
                end_detection_datetime = datetime.now()

                # Format the start and end datettime to "%b %d, %Y - %H:%M:%S" formatted string.
                start_detection_datetime_formatted = start_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")
                end_detection_datetime_formatted = end_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")

                ################## SAVING TABLE_DATA FOR ALL USERS TO BE DISPLAYED IN HISTORY TABLE###############################
                if os.path.exists(TABLE_DATA_JSON_PATH): # If TABLE_DATA_JSON_PATH exists (table_data.json)
                    with open(TABLE_DATA_JSON_PATH) as json_file: # Open it
                        all_table_data_for_all_users = json.load(json_file) # Load it as a dictionary to variable "json_file"
                else:
                    all_table_data_for_all_users = {} # Else, create an empty dictionary
                
                # If username is not existing as a key in all_table_data_for_all_users, create a new key entry with {} as the value
                if username not in all_table_data_for_all_users:
                    all_table_data_for_all_users[username] = {}
                
                try:
                    with open(USER_APP_SETTING_PATH) as json_file_user_settings:
                        all_user_settings = json.load(json_file_user_settings)
                        user_detection_limit = int(all_user_settings[username.replace('@', '')][0]["his_detect"])
                except Exception as error:
                    print(f"Error opening app_settings.config: {error} | Setting user_detection_limit to default (5)")
                    user_detection_limit = 5

                # Sorting the history of detections made by the users in ascending order
                total_detections_made = len(all_table_data_for_all_users[username])
                if total_detections_made >= user_detection_limit:
                    print("AT ITS LIMIT")
                    sorted_user_detections = sorted(all_table_data_for_all_users[username].items(), key=lambda item: datetime.strptime(item[0].split("_")[0], "%b %d, %Y - %H:%M:%S"), reverse=False)
                    sorted_user_detections = sorted_user_detections[1:]
                    sorted_user_detections.append((f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}', table_data_for_all_videos))
                    new_sorted_user_detections = dict(sorted_user_detections)
                    all_table_data_for_all_users[username] = new_sorted_user_detections
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4)

                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)

                    mp4_video_files = [file for file in os.listdir(TEMP_OUTPUT_PATH) if file.endswith(".mp4")]
                    filtered_mp4_video_files = []

                    for file in mp4_video_files:
                        file_identity_data = file.split('_-_')[1]
                        username_in_file_identity_data = file_identity_data.split('-_-')[0]
                        if username.replace('@', '') == username_in_file_identity_data:
                            filtered_mp4_video_files.append(file)
                    
                    sorted_filtered_mp4_video_files = sorted(filtered_mp4_video_files, key=lambda x: datetime.strptime(x.split('-_-')[1].replace(".mp4", ""), "%b-%d--%Y---%H-%M-%S"))
                    os.remove(os.path.join(TEMP_OUTPUT_PATH, sorted_filtered_mp4_video_files[0]))

                else:
                    print("ADDING AN ENTRY")
                    # For a specific username and start and end detection datetime, make the dict value as the dictionary containing all the table data for all the videos processed
                    # all_table_data_for_all_users[username]["input_filter_dict"] = input_filter_dict
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'] = table_data_for_all_videos # Update the table_data dictionary with the key as the input video filepath and table data dictionary as the value
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                
                    
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4) # Serialize it in JSON formatted string

                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)
                ##################################################################################################################

                                # Copy (save) the output video with bounding boxes to TEMP_OUTPUT_PATH - shutil.copy2 keeps the metadata as is
                # TEMP_OUTPUT_PATH contains all the videos of finished detections, it is where the system retrieves a video to be played to a specific timestamp based on selection
                # This adds identity to each video based on the current user and when the detection process started
                try:
                    all_mp4s_in_exp_path = glob.glob(os.path.join(TEMP_PATH, 'output_videos_with_weapons', 'exp', '*.mp4'))
                    filepath_from_temp_folder = all_mp4s_in_exp_path[0]
                    filename = filepath_from_temp_folder.split('\\')[-1].split('.mp4')[0]
                    further_formatted_start_detection_datetime = start_detection_datetime_formatted.replace(",", "-").replace(":", "-").strip().replace(" ", "-")
                    new_filename = f'{filename}_-_{username[1:]}-_-{further_formatted_start_detection_datetime}.mp4'
                    new_filepath_to_save_to = os.path.join(TEMP_OUTPUT_PATH, new_filename)
                    shutil.copy2(filepath_from_temp_folder, new_filepath_to_save_to)
                except PermissionError as e:
                    print(f"Permission Error: {e}")

                ##################################################################################################################

                print(print_msg_box(f'Total Elapsed Time: {total_time}')) # Display total elapsed time

                table_data_and_start_end_datetime_processed = {
                    'table_data' : table_data_for_all_videos,
                    'start_end_datetime_processed' : f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'
                }

                # return table_data_and_start_end_datetime_processed # Return only the current table_data_for_all_videos to be displayed as output including the start and end datetime it was processed

        elif (weapons_to_detect == ['None']) and (list_of_clothings_to_detect != []):  # Executed when only a clothing is the only object selected (no weapon) ###############################################################################
            print('SECOND CONDITIONAL MAIN DRIVER CODE - CLOTHINGS ONLY')
            # Detect clothings and classify their colors in video - uses the video with weapon bounding boxes
            start_time = time.time()

            cleanup_data = {
                'username' : username,
                'start_detection_datetime' : start_detection_datetime
            }

            detect_clothings_and_colors_from_video_and_get_reference_frame_timestamps(input_video_filepath, clothings_to_detect_and_colors, 0.5, *list_of_clothings_to_detect, cleanup_data=cleanup_data, progress_data=progress_data, unix_timestamp_datetime_created=unix_timestamp_datetime_created, project=CLOTHINGS_ONLY_OUTPUT_VIDEOS_FROM_YOLOV5_PATH)
            end_time = time.time()
            print_msg_box(f"detect_clothings_and_colors_from_video_and_get_reference_frame_timestamps() -> Elapsed Time: {round(end_time - start_time, 2)}")
            total_time += round(end_time - start_time, 2)

            clothings_timestamps = extract_timestamps_from_text_file(CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'clothings')
            clothings_data = get_clothings_with_their_colors_timestamps_from_text_file()

            table_data = {} # Create empty dictionary to contain table data for a specific video

            # Return clothings_timestamps (empty dictionary will be returned if this condition is met) if there are no detected clothings.
            if len(clothings_timestamps) <= 0:
                return clothings_timestamps
            else:
                for timestamp in sorted(list(set.union(*clothings_timestamps.values()))): # Iterate through each unique and common timestamps
                    # Structure the table_data dictionary such that:
                    # table_data : {
                    #   timestamp : {
                    #       'weapons' : [],
                    #       'clothing_and_colors' : []
                    #   },
                    #   ...
                    # }
                    table_data[str(timestamp)] = {'weapons': [], 'clothing_and_colors': []}


                for clothing_and_colors_timestamp_item in clothings_data: # Iterate through each timestamp in clothings_data
                    clothing_and_colors_timestamp = str(clothing_and_colors_timestamp_item[1]) # Get the timestamp
                    table_data[clothing_and_colors_timestamp]['clothing_and_colors'].append(clothing_and_colors_timestamp_item) # Append the [[clohing, [color1, color2, ...]], timestamp] element to the corresponding list value of timestamp key

                table_data_for_all_videos[input_video_filepath] = table_data


                # Keep track of the detection process end datetime
                end_detection_datetime = datetime.now()

                # Format the start and end datettime to "%b %d, %Y - %H:%M:%S" formatted string.
                start_detection_datetime_formatted = start_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")
                end_detection_datetime_formatted = end_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")

                ################## SAVING TABLE_DATA FOR ALL USERS TO BE DISPLAYED IN HISTORY TABLE###############################
                if os.path.exists(TABLE_DATA_JSON_PATH): # If TABLE_DATA_JSON_PATH exists (table_data.json)
                    with open(TABLE_DATA_JSON_PATH) as json_file: # Open it
                        all_table_data_for_all_users = json.load(json_file) # Load it as a dictionary to variable "json_file"
                else:
                    all_table_data_for_all_users = {} # Else, create an empty dictionary
                
                # If username is not existing as a key in all_table_data_for_all_users, create a new key entry with {} as the value
                if username not in all_table_data_for_all_users:
                    all_table_data_for_all_users[username] = {}

                try:
                    with open(USER_APP_SETTING_PATH) as json_file_user_settings:
                        all_user_settings = json.load(json_file_user_settings)
                        user_detection_limit = int(all_user_settings[username.replace('@', '')][0]["his_detect"])
                except Exception as error:
                    print(f"Error opening app_settings.config: {error} | Setting user_detection_limit to default (5)")
                    user_detection_limit = 5
                
                # Sorting the history of detections made by the users in ascending order
                total_detections_made = len(all_table_data_for_all_users[username])
                
                # Check if the total detections made by the user exceeds the limit set in the account
                # If the set limit is  greater than or equal than the total detections made, perform the code block under the if statement
                if total_detections_made >= user_detection_limit:
                    print("AT ITS LIMIT - REMOVING OLDEST DETECTION MADE AND REPLACING WITH THE NEW ONE")
                    sorted_user_detections = sorted(all_table_data_for_all_users[username].items(), key=lambda item: datetime.strptime(item[0].split("_")[0], "%b %d, %Y - %H:%M:%S"), reverse=False)
                    sorted_user_detections = sorted_user_detections[1:]
                    sorted_user_detections.append((f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}', table_data_for_all_videos))
                    new_sorted_user_detections = dict(sorted_user_detections)
                    all_table_data_for_all_users[username] = new_sorted_user_detections
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4)

                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)

                    mp4_video_files = [file for file in os.listdir(TEMP_OUTPUT_PATH) if file.endswith(".mp4")]
                    filtered_mp4_video_files = []

                    for file in mp4_video_files:
                        file_identity_data = file.split('_-_')[1]
                        username_in_file_identity_data = file_identity_data.split('-_-')[0]
                        if username.replace('@', '') == username_in_file_identity_data:
                            filtered_mp4_video_files.append(file)
                    
                    sorted_filtered_mp4_video_files = sorted(filtered_mp4_video_files, key=lambda x: datetime.strptime(x.split('-_-')[1].replace(".mp4", ""), "%b-%d--%Y---%H-%M-%S"))
                    os.remove(os.path.join(TEMP_OUTPUT_PATH, sorted_filtered_mp4_video_files[0]))

                # If the set limit is  less than the total detections made, perform the code block under the else statement
                else: 
                    print("ADDING AN ENTRY")
                    # For a specific username and start and end detection datetime, make the dict value as the dictionary containing all the table data for all the videos processed
                    # all_table_data_for_all_users[username]["input_filter_dict"] = input_filter_dict
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'] = table_data_for_all_videos # Update the table_data dictionary with the key as the input video filepath and table data dictionary as the value
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4) # Serialize it in JSON formatted string

                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)
                ##################################################################################################################

                # Copy (save) the output video with bounding boxes to TEMP_OUTPUT_PATH - shutil.copy2 keeps the metadata as is
                # TEMP_OUTPUT_PATH contains all the videos of finished detections, it is where the system retrieves a video to be played to a specific timestamp based on selection
                # This adds identity to each video based on the current user and when the detection process started
                try:
                    all_mp4s_in_exp_path = glob.glob(os.path.join(TEMP_PATH, 'output_videos_with_clothings', 'exp', '*.mp4'))
                    filepath_from_temp_folder = all_mp4s_in_exp_path[0]
                    filename = filepath_from_temp_folder.split('\\')[-1].split('.mp4')[0]
                    further_formatted_start_detection_datetime = start_detection_datetime_formatted.replace(",", "-").replace(":", "-").strip().replace(" ", "-")
                    new_filename = f'{filename}_-_{username[1:]}-_-{further_formatted_start_detection_datetime}.mp4'
                    new_filepath_to_save_to = os.path.join(TEMP_OUTPUT_PATH, new_filename)
                    shutil.copy2(filepath_from_temp_folder, new_filepath_to_save_to)
                except PermissionError as e:
                    print(f"Permission Error: {e}")

                ##################################################################################################################

                print(print_msg_box(f'Total Elapsed Time: {total_time}')) # Display total elapsed time

                table_data_and_start_end_datetime_processed = {
                    'table_data' : table_data_for_all_videos,
                    'start_end_datetime_processed' : f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'
                }

                # return table_data_and_start_end_datetime_processed # Return only the current table_data_for_all_videos to be displayed as output including the start and end datetime it was processed

        else:  # Executed when there are both weapon and clothings selected #################################################################################################################################################################
            print('THIRD CONDITIONAL MAIN DRIVER CODE - BOTH WEAPON AND CLOTHINGS')

            # Construct a dictionary data to be passed as the cleanup data needed when "Cancel" button is clicked
            cleanup_data = {
                'username' : username,
                'start_detection_datetime' : start_detection_datetime
            }
            
            #################################### FIRST STEP - DETECT WEAPON ##################################################################
            # Detect weapons from the current video file being iterated 
            start_time = time.time() # Keep track of the start datetime of the weapon process
            is_frame_in_nightvision_list = detect_weapon_from_video_and_get_reference_frame_timestamps(input_video_filepath, 0.5, *weapons_to_detect, cleanup_data=cleanup_data, progress_data=progress_data, is_weapon_only=False)
            end_time = time.time() # Keep track of the end datetime of the weapon detection process
            print_msg_box(f"detect_weapon_from_video_and_get_reference_frame_timestamps() -> Elapsed Time: {round(end_time - start_time, 2)}")
            total_time += round(end_time - start_time, 2) # Add the elapsed time for weapon detection process to the total time
            ##################################################################################################################################

            #################################### SECOND STEP - DETECT CLOTHINGS ##############################################################
            # Detect clothings and classify their colors in video - uses the video with weapon bounding boxes
            # From the directory where the video file with weapon detections, get the filepath
            filepath_with_weapon_bboxes = ([os.path.join(WEAPON_VIDEO_WITH_BBOXES_SAVE_PATH, file) for file in os.listdir(WEAPON_VIDEO_WITH_BBOXES_SAVE_PATH) if file.endswith('.mp4')][0])
            start_time = time.time() # Keep track of the start datetime of the clothing detection process
            detect_clothings_and_colors_from_video_and_get_reference_frame_timestamps(filepath_with_weapon_bboxes, clothings_to_detect_and_colors, 0.5, *list_of_clothings_to_detect, cleanup_data=cleanup_data, progress_data=progress_data, unix_timestamp_datetime_created=unix_timestamp_datetime_created, is_frame_in_nightvision_list=is_frame_in_nightvision_list, is_clothings_only=False)
            end_time = time.time() # Keep track of the end datetime of the clothing detection process
            print_msg_box(f"detect_clothings_and_colors_from_video_and_get_reference_frame_timestamps() -> Elapsed Time: {round(end_time - start_time, 2)}")
            total_time += round(end_time - start_time, 2) # Add the elapsed time for clothing detection process to the total time

            # Extract the generated timestamps from text files for weapons and clothings and the clothings' corresponding colors
            weapons_timestamps = extract_timestamps_from_text_file(WEAPONS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'weapons')
            clothings_timestamps = extract_timestamps_from_text_file(CLOTHING_COLORS_TIMESTAMP_SECONDS_TEXT_FILE_PATH, 'clothings')
            

            ######################################## SAVING/UPDATING DETECTION TIMESTAMPS RESULTS ###########################################
            # Return an empty dictionary if there are no detected weapons and clothings.
            if (len(weapons_timestamps) <= 0) and (len(clothings_timestamps) <= 0):
                return {}
            else: # Otherwise...
                # Get the unique and common timestamps of detected weapons and clothings
                unique_and_common_timestamps = get_unique_and_common_timestamps(clothings_timestamps, weapons_timestamps)
                # Get the weapon timestamps only
                weapons_data = get_weapons_with_their_timestamps_from_text_file()
                # Get the clothing timestamps only
                clothings_data = get_clothings_with_their_colors_timestamps_from_text_file()
                table_data = {} # Create empty dictionary to contain table data for a specific video
                # Iterate through each unique and common timestamps
                for timestamp in unique_and_common_timestamps: 
                    # Structure the table_data dictionary such that:
                    # table_data : {
                    #   timestamp1 : {
                    #       'weapons' : [],
                    #       'clothing_and_colors' : []
                    #   },
                    #   timestamp2 : {
                    #       'weapons' : [],
                    #       'clothing_and_colors' : []
                    #   },
                    #   ...
                    # }
                    table_data[str(timestamp)] = {'weapons': [], 'clothing_and_colors': []} 

                for weapon_timestamp_item in weapons_data: # Iterate through each timestamp in weapons_data
                    weapon_timestamp = str(weapon_timestamp_item[1]) # Get the timestamp
                    table_data[weapon_timestamp]['weapons'].append(weapon_timestamp_item) # Append the [weapon, timestamp] element to the corresponding list value of timestamp key

                for clothing_and_colors_timestamp_item in clothings_data: # Iterate through each timestamp in clothings_data
                    clothing_and_colors_timestamp = str(clothing_and_colors_timestamp_item[1]) # Get the timestamp
                    table_data[clothing_and_colors_timestamp]['clothing_and_colors'].append(clothing_and_colors_timestamp_item) # Append the [[clohing, [color1, color2, ...]], timestamp] element to the corresponding list value of timestamp key

                # Append the filled table data as value to the key-value pair in the table_data_for_all_videos with input_video_filepath as the key
                table_data_for_all_videos[input_video_filepath] = table_data

                # Keep track of the detection process end datetime
                end_detection_datetime = datetime.now()

                # Format the start and end datettime to "%b %d, %Y - %H:%M:%S" formatted string.
                start_detection_datetime_formatted = start_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")
                end_detection_datetime_formatted = end_detection_datetime.strftime("%b %d, %Y - %H:%M:%S")

                ################## SAVING TABLE_DATA FOR ALL USERS TO BE DISPLAYED IN HISTORY TABLE ###############################
                if os.path.exists(TABLE_DATA_JSON_PATH): # If TABLE_DATA_JSON_PATH exists (.../table_data.json)
                    with open(TABLE_DATA_JSON_PATH) as json_file: # Open it
                        all_table_data_for_all_users = json.load(json_file) # Load it as a dictionary to variable "json_file"
                else:
                    all_table_data_for_all_users = {} # Else, create an empty dictionary
                
                # If username is not existing as a key in all_table_data_for_all_users, create a new key entry with {} as the value
                if username not in all_table_data_for_all_users:
                    all_table_data_for_all_users[username] = {}
                
                # Read the user detection limit in the settings to update the display of the history table
                try:
                    with open(USER_APP_SETTING_PATH) as json_file_user_settings:
                        all_user_settings = json.load(json_file_user_settings)
                        user_detection_limit = int(all_user_settings[username.replace('@', '')][0]["his_detect"])
                # Set the user detection limit is there no existing value in the settings (Default is 5 detections to be displayed in history table)
                except Exception as error: 
                    print(f"Error opening app_settings.config: {error} | Setting user_detection_limit to default (5)")
                    user_detection_limit = 5

                # Handles detection capping - both in .json file and .mp4 files with bboxes
                # The exact implementation is applied for other conditionals.
                # Sorting the history of detections made by the users in ascending order
                total_detections_made = len(all_table_data_for_all_users[username])
                
                # Deleting the most old detection in .json file and output .mp4 video in temp_output directory
                if total_detections_made >= user_detection_limit:
                    print("AT ITS LIMIT")
                    # Updating the detections made by the user and the .json file in general
                    # Sort them in ascending order based on the datetime the detection(s) was/were started
                    sorted_user_detections = sorted(all_table_data_for_all_users[username].items(), key=lambda item: datetime.strptime(item[0].split("_")[0], "%b %d, %Y - %H:%M:%S"), reverse=False)
                    # Remove the first entry
                    sorted_user_detections = sorted_user_detections[1:]
                    # Add the new one
                    sorted_user_detections.append((f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}', table_data_for_all_videos))
                    # Make the sorted as a dictionary
                    new_sorted_user_detections = dict(sorted_user_detections)
                    # Replace the history of detections for the current user with the updated one
                    all_table_data_for_all_users[username] = new_sorted_user_detections
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                    # Save the .json file
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4)
                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)
                    
                    # Removal of the oldest .mp4 output video in temp_output directory
                    mp4_video_files = [file for file in os.listdir(TEMP_OUTPUT_PATH) if file.endswith(".mp4")] # Filter .mp4 videos in temp_output directory
                    filtered_mp4_video_files = [] # Create an empty list to store the output videos with bboxes with respect to the current user

                    # Iterate through each file and verify if it belongs to the current user
                    for file in mp4_video_files:
                        file_identity_data = file.split('_-_')[1] 
                        username_in_file_identity_data = file_identity_data.split('-_-')[0]
                        if username.replace('@', '') == username_in_file_identity_data:
                            filtered_mp4_video_files.append(file) # Append if it belongs to the current user
                    
                    # Sort them in ascending order based on the datetime the detection process started
                    sorted_filtered_mp4_video_files = sorted(filtered_mp4_video_files, key=lambda x: datetime.strptime(x.split('-_-')[1].replace(".mp4", ""), "%b-%d--%Y---%H-%M-%S"))
                    # Remove the first entry - addition of the new video will on the succeeding try-except block below the else statement
                    os.remove(os.path.join(TEMP_OUTPUT_PATH, sorted_filtered_mp4_video_files[0]))

                else: # Else statement if the cap/limit is not yet reached
                    print("ADDING AN ENTRY")
                    # Update the .json file normally (addition of new data for the current user)
                    # For a specific username and start and end detection datetime, make the dict value as the dictionary containing all the table data for all the videos processed
                    # all_table_data_for_all_users[username]["input_filter_dict"] = input_filter_dict
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'] = table_data_for_all_videos # Update the table_data dictionary with the key as the input video filepath and table data dictionary as the value
                    all_table_data_for_all_users[username][f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}']["input_filter_dict"] = input_filter_dict
                    updated_json = json.dumps(all_table_data_for_all_users, indent=4) # Serialize it in JSON formatted string

                    with open(os.path.join(TABLE_DATA_JSON_PATH), 'w') as json_file: # Save the serialized JSON formatted string to TABLE_DATA_JSON_PATH
                        json_file.write(updated_json)
                ##################################################################################################################
                
                # Copy (save) the output video with bounding boxes to TEMP_OUTPUT_PATH - shutil.copy2 keeps the metadata as is
                # TEMP_OUTPUT_PATH contains all the videos of finished detections, it is where the system retrieves a video to be played to a specific timestamp based on selection
                # This adds identity to each video based on the current user and when the detection process started
                try:
                    all_mp4s_in_exp_path = glob.glob(os.path.join(TEMP_PATH, 'output_videos_with_clothings_and_weapons', 'exp', '*.mp4'))
                    filepath_from_temp_folder = all_mp4s_in_exp_path[0]
                    filename = filepath_from_temp_folder.split('\\')[-1].split('.mp4')[0]
                    further_formatted_start_detection_datetime = start_detection_datetime_formatted.replace(",", "-").replace(":", "-").strip().replace(" ", "-")
                    new_filename = f'{filename}_-_{username[1:]}-_-{further_formatted_start_detection_datetime}.mp4'
                    new_filepath_to_save_to = os.path.join(TEMP_OUTPUT_PATH, new_filename)
                    shutil.copy2(filepath_from_temp_folder, new_filepath_to_save_to)
                except PermissionError as e:
                    print(f"Permission Error: {e}")

                ##################################################################################################################

                print(print_msg_box(f'Total Elapsed Time: {total_time}')) # Display total elapsed time

                # Return the table_data that contains the data regarding the detection for all videos that were applied with object detection
                # Return the start and end datetime (string formatted) as well
                # Pack them a dictionary to be returned
                table_data_and_start_end_datetime_processed = {
                    'table_data' : table_data_for_all_videos,
                    'start_end_datetime_processed' : f'{start_detection_datetime_formatted}_{end_detection_datetime_formatted}'
                }
    
    # This script is ran as a thread, after it is finished, return the table_data_and_start_end_datetime_process dictionary
    return table_data_and_start_end_datetime_processed


# if __name__ == '__main__':

# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Pictures\Camera Roll\WIN_20230721_22_50_48_Pro.mp4'
# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Pictures\Camera Roll\WIN_20230718_16_38_39_Pro.mp4'
# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Downloads\Untitled.mp4'
# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Videos\Overwatch 2\Overwatch 2 2023.01.02 - 20.40.27.04.DVR.mp4'
# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Pictures\Camera Roll\WIN_20230721_18_20_50_Pro.mp4'  # Change accordingly
# #     # INPUT_VIDEO_FILEPATH = r'C:\Users\Jco\Downloads\19sec.mp4'

#         #=== INPUT GUIDE ===#
#     # Separate comma in the list if there is more than one weapon or clothings to detect (e.g., [0, 1])

#     # weapons_class_mapping = {
#     #   'all' = None
#     #   'handgun' = 0,
#     #   'knife' = 1
#     # }

#     # clothings_class_mapping = {
#     #     'sleeved_shirt' : 0,
#     #     'sleeveless_top' : 1,
#     #     'outwear' : 2,
#     #     'shorts' : 3,
#     #     'trousers' : 4,
#     #     'skirt' : 5,
#     #     'dress' : 6
#     # }

#     weapons_to_detect = [0] # 0=handgun, 1=knife, None=all (default) # Change accordingly
#     upper_clothings_to_detect = [0]
#     lower_clothings_to_detect = [3]
#     upper_clothings_color = 'grey'
#     lower_clothings_color = 'orange_brown'

#     clothings_to_detect_and_colors = {
#         reversed_clothings_class_mapping[upper_clothings_to_detect[0]] : upper_clothings_color,
#         reversed_clothings_class_mapping[lower_clothings_to_detect[0]] : lower_clothings_color
#     }
    
#     reconstruction_duration = 5
    
#     sample_vids = [
#         r'C:\Users\Jco\Pictures\Camera Roll\WIN_20230921_16_15_27_Pro.mp4',
#         # r'C:\Users\Jco\Pictures\Camera Roll\WIN_20230921_16_17_25_Pro.mp4'
#     ]

#     main_driver_code(sample_vids, weapons_to_detect, clothings_to_detect_and_colors, reconstruction_duration)