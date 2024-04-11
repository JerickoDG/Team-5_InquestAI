import fast_colorthief
import numpy as np

"""
Accepts an image numpy array in three-dimension
Returns a list containing the dominant color
"""
def get_top_n_colors(image_array):

    # key -> color_rangenum ; value -> (lower bound hue value, upper bound hue value)
    color_mapping = {
        'red_1': (0, 10),
        'red_2': (355, 359),
        'orange_3': (11, 20),
        'orange_1': (21, 34),
        'yellow': (35, 60),
        'green_2': (61, 80), 
        'green_1': (81, 140),
        'green_3': (141, 169), 
        'green_4': (170, 200), 
        'blue_3': (201, 220), 
        'blue_1': (221, 240),
        'purple_1': (241, 280), 
        'purple_2': (281, 320), 
        'purple_3': (321, 330), 
        'red_4': (331, 345), 
        'red_5': (346, 355)
    }

    height, width, _ = image_array.shape # Get height and width of the image
     # Add alpha channel (RGB to RGBA) - Full opacity (alpha = 255) because get_dominant_color() from fast_colorthief.py only accepts image numpy array in RGBA
    image_array = np.concatenate((image_array, np.full((height, width, 1), 255, dtype=np.uint8)), axis=2)


    ##################################################### DOMINANT COLOR CHECKING #####################################################
    dominant_color = [] # Create empty list that will contain the dominant color
    dominant_color_rgb = fast_colorthief.get_dominant_color(image_array, 5) # Get dominant color - returns (R, G, B)
    dominant_color_hsv = [rgb_to_hsv(dominant_color_rgb)] # Convert (R, G, B) to [H, S, V]
    dch = int(dominant_color_hsv[0][0]) # Extract hue
    dcs = int(dominant_color_hsv[0][1]) # Extract saturation
    dcv = int(dominant_color_hsv[0][2]) # Extract value

    if (dcv > 25) and (dcs <= 15): # Check if achromatic - grey/white
        dominant_color.append("Grey/White")
    elif dcv <= 25: # Check if achromatic - black
        dominant_color.append("Black")
    else: # Else statement means that the color has an emphasized hue (i.e., chromatic)
        for hue_name, hue_range in color_mapping.items(): # Iterate through each key-value pair in color_mapping
            hr = range(hue_range[0], hue_range[1]+1) # Get the range of the color range being iterated
            
            if (dch in hr): # If hue value is inside the current hue range, add the name of the color
                hue_name = hue_name.replace('_', ' ').title()
                hue_name = hue_name.split(' ')[0]
                dominant_color.append(hue_name)

    return dominant_color # Return the list containing the dominant color
    ###################################################################################################################################

"""
Converts RGB tuple to HSV
Accepts RGB tuple
Returns three values (i.e., H, S, V)
"""
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