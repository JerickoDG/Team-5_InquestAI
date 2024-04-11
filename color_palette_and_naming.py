import extcolors
import numpy as np
import cv2
import joblib
from PIL import Image
from tensorflow import keras
from keras.models import load_model

# model = load_model(r'D:\extract-colors-py\colors_model.h5')
# scaler = joblib.load(r'D:\extract-colors-py\scaler.pkl')

model = joblib.load(r'D:\extract-colors-py\model_pipeline (2).pkl')

# color_class_encoding = {
#     0: 'Black',
#     1: 'Blue',
#     2: 'Brown',
#     3: 'Green',
#     4: 'Grey',
#     5: 'Orange',
#     6: 'Pink',
#     7: 'Purple',
#     8: 'Red',
#     9: 'White',
#     10: 'Yellow'
#  }


def generate_names_from_palettes(image_array, top_n=5):
    rgb_colors_and_pixel_count = extcolors.extract_from_image(image_array, tolerance=20)[0]
    colorname_predictions = []

    for rgb_color_pix in rgb_colors_and_pixel_count:
        rgb_color = rgb_color_pix[0]
        pixel_count = rgb_color_pix[1]
        # scaled_input = scaler.transform([rgb_color])
        predicted_color = model.predict([rgb_color])[0]

        colorname_predictions.append(predicted_color)

    return list(dict.fromkeys(colorname_predictions))


# def generate_names_from_palettes(image_array, top_n=5):
#     rgb_colors_and_pixel_count = extcolors.extract_from_image(image_array, tolerance=20)[0]
#     colorname_predictions = []

#     for rgb_color_pix in rgb_colors_and_pixel_count:
#         rgb_color = rgb_color_pix[0]
#         pixel_count = rgb_color_pix[1]
#         scaled_input = scaler.transform([rgb_color])
#         prediction = np.argmax(model.predict(scaled_input))

#         if color_class_encoding[prediction] not in [i[0] for i in colorname_predictions]:
#             colorname_predictions.append((color_class_encoding[prediction], pixel_count))
    

#     return [i[0] for i in colorname_predictions]


# print(generate_names_from_palettes(Image.open(r'C:\Users\Jco\Downloads\Screenshot 2023-08-11 220355.png'), top_n=5))
# print(np.argmax(model.predict([[170, 56, 44]])))
