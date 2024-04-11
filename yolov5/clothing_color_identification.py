from colorthief import ColorThief
from PIL import Image
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
import fast_colorthief
import time
import numpy as np
import joblib

# model = joblib.load(r'D:\extract-colors-py\model_pipeline (2).pkl')

# def color_distance(rgb1, rgb2):
#     r1, g1, b1 = rgb1
#     r2, g2, b2 = rgb2
#     return (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2

# def map_to_color(rgb_color):
#     r, g, b = rgb_color

#     color_map = {
#         'yellow': ((255, 200, 0), (255, 255, 100)),
#         'orange': ((255, 120, 0), (255, 180, 60)),
#         'red': ((200, 0, 0), (255, 100, 100)),
#         'violet': ((150, 50, 150), (200, 150, 200)),
#         'blue': ((0, 0, 180), (100, 100, 255)),
#         'green': ((0, 100, 0), (100, 200, 100)),
#         'black': ((0, 0, 0), (60, 60, 60)),
#         'white': ((200, 200, 200), (255, 255, 255)),
#         'brown': ((100, 40, 0), (180, 90, 40)),
#         'grey': ((100, 100, 100), (180, 180, 180))
#     }

#     min_distance = float('inf')
#     closest_color = None

#     for color_name, (lower, upper) in color_map.items():
#         if all(lower[i] <= c <= upper[i] for i, c in enumerate((r, g, b))):
#             return color_name

#         distance = color_distance((r, g, b), lower)
#         if distance < min_distance:
#             min_distance = distance
#             closest_color = color_name

#     return closest_color

# def get_top_n_colors(image_array, n=3):
#     # color_thief = ColorThief(image_array)
#     # palette = color_thief.get_palette(color_count=n)
#     height, width, _ = image_array.shape
#     image_array = np.concatenate((image_array, np.full((height, width, 1), 255, dtype=np.uint8)), axis=2) # Add alpha channel (RGB to RGBA) - Full opacity (alpha = 255)
#     palette = fast_colorthief.get_palette(image_array, 5)
#     top_n_colors = [model.predict([color])[0] for color in palette]
#     return list(dict.fromkeys(top_n_colors))


def get_top_n_colors(image_array):
    color_mapping = {
        'red_1': (0, 10),
        'red_2': (355, 359),
        'red_orange': (11, 20),
        'orange_brown': (21, 40),
        'orange_yellow': (41, 50),
        'yellow': (51, 60),
        'yellow_green': (61, 80),
        'green': (81, 140),
        'green_cyan': (141, 169),
        'cyan': (170, 200),
        'cyan_blue': (201, 220),
        'blue': (221, 240),
        'blue_magenta': (241, 280),
        'magenta': (281, 320),
        'magenta_pink': (321, 330),
        'pink': (331, 345),
        'pink_red': (346, 355)
    }

    # color_mapping = {
    #     'red_1' : (0, 20),
    #     'red_2' : (321, 359),
    #     'orange_brown_yellow' : (21, 60),
    #     'green' : (61, 169),
    #     'blue' : (170, 240),
    #     'violet_magenta' : (241, 320)
    # } 

    height, width, _ = image_array.shape
    image_array = np.concatenate((image_array, np.full((height, width, 1), 255, dtype=np.uint8)), axis=2) # Add alpha channel (RGB to RGBA) - Full opacity (alpha = 255)
    palette = fast_colorthief.get_palette(image_array, 5)

    colors = []

    palette_hsv = [rgb_to_hsv(color) for color in palette]
    for color in palette_hsv:

        hue = int(color[0])
        saturation = int(color[1])
        value = int(color[2])

        if (15 < value < 90) and (saturation <=15):
            colors.append('Grey')
        elif (value >= 90) and (saturation <=15):
            colors.append('White')
        elif value <= 15:
            colors.append('Black')
        else:
            for hue_name, hue_range in color_mapping.items():
                hr = range(hue_range[0], hue_range[1]+1)
                
                if (hue in hr):
                    hue_name = hue_name.replace('_', ' ').title()
                    if 'Red' in hue_name:
                        hue_name = hue_name.split(' ')[0]
                    colors.append(hue_name)
    
    return list(dict.fromkeys(colors))


def rgb_to_hsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    max_value = max(r, g, b)
    min_value = min(r, g, b)
    delta = max_value - min_value

    if max_value == 0 or delta == 0:
        h = s = 0
    else:
        s = delta / max_value
        if max_value == r:
            h = 60 * ((g - b) / delta % 6)
        elif max_value == g:
            h = 60 * ((b - r) / delta + 2)
        else:
            h = 60 * ((r - g) / delta + 4)
    h = (h + 360) % 360

    return h, s * 100, max_value * 100



# def map_rgb_to_color(rgb_value):
#     color_map = {
#         'yellow': ((255, 200, 0), (255, 255, 100)),
#         'orange': ((255, 120, 0), (255, 180, 60)),
#         'red': ((200, 0, 0), (255, 100, 100)),
#         'violet': ((150, 50, 150), (200, 150, 200)),
#         'blue': ((0, 0, 180), (100, 100, 255)),
#         'green': ((0, 100, 0), (100, 200, 100)),
#         'black': ((0, 0, 0), (60, 60, 60)),
#         'white': ((200, 200, 200), (255, 255, 255)),
#         'brown': ((100, 40, 0), (180, 90, 40)),
#         'grey': ((100, 100, 100), (180, 180, 180))
#     }
        
#     for color_name, color_range in color_map.items():
#         lower_bound, upper_bound = color_range
#         if all(lower_bound <= rgb_value) and all(rgb_value <= upper_bound):
#             return color_name
#     return "unknown"

# def get_top_n_colors_KMeans(image_array, n=3):
#     kmeans = KMeans(n_clusters=n, random_state=42)
#     kmeans.fit(image_array.reshape(-1, 3))
#     cluster_centers = kmeans.cluster_centers_.astype(int)
#     top_n_colors = [map_rgb_to_color(center) for center in cluster_centers]
#     return top_n_colors