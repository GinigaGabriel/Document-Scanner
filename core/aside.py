import cv2
import datetime
import logging
import numpy

LOGGER = logging.getLogger('root')


def save_key(data, output_location):
    try:
        photo_name = f"{(datetime.datetime.now()).strftime('%H %M %S')}.png"
        image_path = str(output_location / photo_name)
        cv2.imwrite(image_path, data[0], params=(cv2.IMWRITE_PNG_COMPRESSION, 0))

        photo_name_black_and_white = f"{(datetime.datetime.now()).strftime('%H %M %S')} B.png"
        image_path_black_white = str(output_location / photo_name_black_and_white)
        cv2.imwrite(image_path_black_white, data[1], params=(cv2.IMWRITE_PNG_COMPRESSION, 0))
        print(image_path)
    except Exception as e:
        LOGGER.error(e)


def draw_on_image(img, message, **kwargs):
    background = kwargs.get('background', False)

    if background:
        r_img = cv2.rectangle(img, (5, 5), (int(len(message) * 15 + 20), 50), (255, 255, 255), thickness=-1)

    r_img = cv2.putText(img, message, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

    return r_img


def reorder(points):
    points = points.reshape((4, 2))
    new_points = numpy.zeros((4, 1, 2), dtype=numpy.int32)
    add = points.sum(1)

    new_points[0] = points[numpy.argmin(add)]
    new_points[3] = points[numpy.argmax(add)]
    diff = numpy.diff(points, axis=1)
    new_points[1] = points[numpy.argmin(diff)]
    new_points[2] = points[numpy.argmax(diff)]

    return new_points


def hor_stack_imgs(list_of_imgs: list):
    horizontal_stack = None
    for x in range(0, len(list_of_imgs)):
        if x == 0:
            horizontal_stack = list_of_imgs[x]
        else:
            horizontal_stack = numpy.hstack((horizontal_stack, list_of_imgs[x]))
    return horizontal_stack


def draw_rectangle(img, poligon, thickness):
    img = cv2.drawContours(img, poligon, -1, (0, 255, 0), 20)
    cv2.line(img, (poligon[0][0][0], poligon[0][0][1]), (poligon[1][0][0], poligon[1][0][1]), (0, 255, 0),
             thickness)
    cv2.line(img, (poligon[0][0][0], poligon[0][0][1]), (poligon[2][0][0], poligon[2][0][1]), (0, 255, 0),
             thickness)
    cv2.line(img, (poligon[3][0][0], poligon[3][0][1]), (poligon[2][0][0], poligon[2][0][1]), (0, 255, 0),
             thickness)
    cv2.line(img, (poligon[3][0][0], poligon[3][0][1]), (poligon[1][0][0], poligon[1][0][1]), (0, 255, 0),
             thickness)

    return img


def generate_na(original):
    first = (int(original.shape[0] / 7), int(original.shape[1] / 1.5))
    second = (int(original.shape[0] / 7), int(original.shape[1] / 1.5 + 100))
    empty_img = numpy.zeros((original.shape[0], original.shape[1], original.shape[2]), numpy.uint8)
    empty_img = cv2.putText(empty_img, "Can't find the document.", first, cv2.FONT_HERSHEY_SIMPLEX, 1.7,
                            (255, 255, 255), 2)
    empty_img = cv2.putText(empty_img, "Try to adjust the dials on the right.", second, cv2.FONT_HERSHEY_SIMPLEX,
                            1.5, (255, 255, 255), 2)
    return empty_img
