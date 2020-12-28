from core.root import *
import cv2
import datetime

def find_key(k):
    print(k)

def save_key(data,output_location):
    try:

        photo_name = f"{(datetime.datetime.now()).strftime('%d%B%Y_%H%M%S')}.png"
        image_path = str(output_location / photo_name)
        cv2.imwrite(image_path, data[1], params=(cv2.IMWRITE_PNG_COMPRESSION, 0))

        photo_name_black_and_white = f"{(datetime.datetime.now()).strftime('%d%B%Y_%H%M%S')}_gray.png"
        image_path_black_white = str(output_location / photo_name_black_and_white)
        cv2.imwrite(image_path_black_white, data[0], params=(cv2.IMWRITE_PNG_COMPRESSION, 0))

    except Exception as e:
        print(e)