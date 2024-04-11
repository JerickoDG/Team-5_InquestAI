# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""
Run YOLOv5 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     screen                          # screenshot
                                                     path/                           # directory
                                                     list.txt                        # list of images
                                                     list.streams                    # list of streams
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s_openvino_model     # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
                                 yolov5s_paddle_model       # PaddlePaddle
"""

import argparse
import os
import platform
import sys
import datetime
import pytz
import numpy as np
import math
import json
from pathlib import Path
from win32com.propsys import propsys, pscon
from PyQt6.QtCore import pyqtSignal

import cv2
from moviepy.editor import VideoFileClip
from moviepy.editor import ImageSequenceClip
from datetime import datetime

import torch

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode


MAIN_PATH = os.getcwd()
TEMP_PATH = os.path.join(MAIN_PATH, 'temp')
TEMP_OUTPUT_PATH = os.path.join(MAIN_PATH, 'temp_output')


@smart_inference_mode()
def run(
        weights=ROOT / 'yolov5s.pt',  # model path or triton URL
        source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        save_timestamps=True, # ADDED TO SAVE TIMESTAMPS WHERE WEAPONS ARE FOUND
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        progress_data=None,
        is_weapon_only=True,
        cleanup_data=None
):
    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
    screenshot = source.lower().startswith('screen')
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=False, exist_ok=False)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    bs = 1  # batch_size
    if webcam:
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = len(dataset)
    elif screenshot:
        dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())

    frame_counter = 0
    total_frame_count = cv2.VideoCapture(source).get(cv2.CAP_PROP_FRAME_COUNT)
    # seconds_timestamp_of_frames_with_bboxes = []
    stored_seconds_to_avoid_ms_duplicated_cropped_frames = []
    # input_video_fps = get_video_fps(source)
    # input_video_creation_timestamp_unix = os.path.getctime(source)
    try:
        properties = propsys.SHGetPropertyStoreFromParsingName(source.replace('/', '\\'))
        dt_property = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
        input_video_creation_timestamp_unix = dt_property.timestamp() - 2 # 2 seconds is the offset from the time the media was created
    except Exception as error:
        print(f"Error: {error}")

    is_frame_in_nightvision_list = []

    # Read the first frame to get dimensions and frame rate
    cap = cv2.VideoCapture(source)
    ret, first_frame = cap.read()

    # Check if the video capture was successful and the first frame exists
    if not ret or first_frame is None:
        raise ValueError("Error reading the first frame from the video")

    frames = [first_frame]

    for path, im, im0s, vid_cap, s in dataset:

        # Check if the frame is in night vision - this is passed to detect_clothings.py
        is_nightvision = (im0s[:,:,0]==im0s[:,:,1]).all()
        is_frame_in_nightvision_list.append(is_nightvision)

        frame_counter += 1
        with dt[0]:
            im = torch.from_numpy(im).to(model.device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                        with open(f'{txt_path}.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                    if save_crop:
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
                    if save_timestamps:
                        unix_timestamp_from_frame = input_video_creation_timestamp_unix + (vid_cap.get(cv2.CAP_PROP_POS_MSEC)/1000)
                        unix_timestamp_from_frame_rounded = math.floor(unix_timestamp_from_frame)
                        # seconds_from_timestamp = get_seconds_from_timestamp(timestamp_from_frame_number)
                        # seconds_component_of_timestamp = timestamp_from_frame_number.replace(':', '-').split('-')[-1]
                        namesc_and_timestamp = f'{names[c]}_{unix_timestamp_from_frame_rounded}'
                        if namesc_and_timestamp not in stored_seconds_to_avoid_ms_duplicated_cropped_frames:
                            stored_seconds_to_avoid_ms_duplicated_cropped_frames.append(namesc_and_timestamp)
                            with open(os.path.join(TEMP_PATH, 'file_weapons.txt'), 'a') as f:
                                f.write(f'{names[c], unix_timestamp_from_frame_rounded}\n')

            # Stream results
            im0 = annotator.result()

            if view_img:
                if platform.system() == 'Linux' and p not in windows:
                    windows.append(p)
                    cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                    cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            # print(fps)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    ###
                    # frame_num_to_timestamp_txt = get_timestamp_from_frame(frame_counter, fps)
                    unix_timestamp_frame_video = input_video_creation_timestamp_unix + (vid_cap.get(cv2.CAP_PROP_POS_MSEC)/1000)
                    utc_timestamp_frame = datetime.fromtimestamp(unix_timestamp_frame_video)
                    im0 = cv2.putText(im0, f'{utc_timestamp_frame} {unix_timestamp_frame_video}', (50,50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    # im0 = cv2.putText(im0, f'{datetime.fromtimestamp(input_video_creation_timestamp_unix + (vid_cap.get(cv2.CAP_PROP_POS_MSEC)/1000))}', (50,150), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    ###
                    # frames.append(cv2.resize(cv2.cvtColor(im0, cv2.COLOR_BGR2RGB), (w, h)))
                    vid_writer[i].write(im0)

        # Print time (inference-only)
        # if len(det) > 0:
        #     seconds_timestamp_of_frames_with_bboxes.append(frame_num_to_timestamp_txt)
        LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

        # Conditionals for setting the progress bar value if clothing only or detecting both weapons and clothing
        if is_weapon_only:
            progress_bar_value_points = np.round(np.arange(0, 1.01, 0.5/progress_data['num_of_input_video_filepaths']), 2)
            progress_bar_min_value = progress_bar_value_points[progress_data['zero_indexed_nth_video_filepath']] * 100
            progress_bar_max_value = progress_bar_value_points[progress_data['zero_indexed_nth_video_filepath'] + 2] * 100
            progress_value_count = map_value_to_range(frame_counter, from_min=0, from_max=total_frame_count, to_min=progress_bar_min_value, to_max=progress_bar_max_value)
            progress_data['progress_callback'].emit(progress_value_count)
                
        else:
            progress_bar_value_points = np.round(np.arange(0, 1.01, 0.5/progress_data['num_of_input_video_filepaths']), 2)
            progress_bar_min_value = progress_bar_value_points[progress_data['zero_indexed_nth_video_filepath']] * 100
            progress_bar_max_value = progress_bar_value_points[progress_data['zero_indexed_nth_video_filepath'] + 1] * 100
            progress_value_count = map_value_to_range(frame_counter, from_min=0, from_max=total_frame_count, to_min=progress_bar_min_value, to_max=progress_bar_max_value)
            progress_data['progress_callback'].emit(progress_value_count)
        

        # I made the callback function as a value in a dictionary so I called it using the key and added "()" to obtain the self.isInterruptionRequested (boolean)
        if progress_data['cancel_callback']():
            print(f"progress_data['cancel_callback'] = {progress_data['cancel_callback']()} ||| Cancelled from detect_weapon.py") # Display to know the value of self.isInterruptionRequested (boolean)

            # Get the contents of the cleanup data dictionary
            username = cleanup_data["username"]
            start_detection_datetime = cleanup_data["start_detection_datetime"]

            # Read the contents of table_data.json
            try:
                with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'r') as table_data_json_r:
                    table_data = json.load(table_data_json_r)
            except:
                print("Error opening table_data.json")

            # print(f"(BEFORE) Detection datetimes in table_data.json: {table_data[username].keys()} ||| Length: {len(table_data[username].keys())}")
            filtered_table_user_specific_data = {} # Assign an empty dictionary to store the reverted version of the dictionary
            # Iterate through each key-value pair, if the start datetime in key (start datetime_end datetime) is equal to the cleanup_data["start_detection-datetime"], remove it (don't include)
            for key, value in table_data[username].items():
                # print(start_detection_datetime.replace(microsecond=0), datetime.strptime(key.split('_')[0], '%b %d, %Y - %H:%M:%S').replace(microsecond=0))
                if datetime.strptime(key.split('_')[0], '%b %d, %Y - %H:%M:%S').replace(microsecond=0) != start_detection_datetime.replace(microsecond=0):
                    filtered_table_user_specific_data[key] = value

            # print(f"(AFTER) Detection datetimes in table_data.json: {filtered_table_user_specific_data.keys()} ||| Length: {len(filtered_table_user_specific_data)}")
            
            # Update table_data with the newly filtered (reverted) one
            table_data[username] = filtered_table_user_specific_data

            # Overwrite the contents of table_data.json with the updated (reverted) table_data
            try:
                with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'w') as table_data_json_w:
                    json.dump(table_data, table_data_json_w)
            except:
                print("Error opening table_data.json")


            raise Exception # raise Exception to that it falls back instantly to the On_Progress.py


    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)

    # unique_timestamps = list(set(seconds_timestamp_of_frames_with_bboxes))
    # unique_timestamps_in_seconds = [get_seconds_from_timestamp(i) for i in unique_timestamps]
    # return unique_timestamps_in_seconds

    # Create a video clip from the list of frames using ImageSequenceClip
    # video_clip = ImageSequenceClip(frames, fps=fps)

    # Write the video clip to the output file
    # video_clip.write_videofile(save_path, codec='libx264')
    # video_clip.write_videofile(r'C:\Users\Jco\Pictures\Camera Roll\test\loool.mp4', codec='libx264')

    # Close MoviePy resources
    # video_clip.close()

    return is_frame_in_nightvision_list


def map_value_to_range(value, from_min, from_max, to_min, to_max):
    # Calculate the percentage of 'value' in the original range
    percentage = (value - from_min) / (from_max - from_min)

    # Map the percentage to the new range
    mapped_value = to_min + percentage * (to_max - to_min)

    # Ensure the mapped value stays within the target range
    return int(max(to_min, min(mapped_value, to_max)))


def get_video_fps(input_video_filepath):
    cap = cv2.VideoCapture(input_video_filepath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # video_clip = VideoFileClip(input_video_filepath)
    # fps = video_clip.fps
    # video_clip.reader.close()
    return fps

def get_timestamp_from_frame(frame_count, fps):
    total_seconds = frame_count / fps
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    timestamp = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    return timestamp

def get_seconds_from_timestamp(timestamp):
    dt_obj = datetime.strptime(timestamp, '%H:%M:%S')
    seconds = dt_obj.hour * 3600 + dt_obj.minute * 60 + dt_obj.second
    return seconds


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path or triton URL')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob/screen/0(webcam)')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--save-timestamps', action='store_true', help='save timestamps where weapons found')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(ROOT / 'requirements.txt', exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == '__main__':
    opt = parse_opt()
    main(opt)