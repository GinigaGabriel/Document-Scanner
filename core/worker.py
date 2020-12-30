import time
import numpy
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from ui.gui import *
from core.needed import *

from core.aside import *

PREVIEW_TAGS = [["Original", "Threshold", "Contours"],
                ["Biggest Contour", "Warp Prespective", "Adaptive Threshold"]]


class WorkerThread(QThread):
    result = pyqtSignal(object)
    resource = None
    eq_hist = False
    median_blur = 0
    save_flag = False
    camera_flag = None
    output = None
    dial_thresh_x = 0
    dial_thresh_y = 0

    dial_min_area = 0
    dial_max_area = 0

    def set_eq_hist(self, new_value):
        if self.eq_hist:
            self.eq_hist = True
        else:
            self.eq_hist = False

    def set_save_flag(self, new_value):
        if self.isRunning():
            self.save_flag = True

    def set_dial_thresh_x(self, new_value):
        self.dial_thresh_x = new_value

    def set_kernel(self, new_value):
        self.median_blur = new_value

    def set_dial_thresh_y(self, new_value):
        self.dial_thresh_y = new_value

    def set_dial_max_area(self, new_value):
        self.dial_max_area = new_value

    def set_dial_min_area(self, new_value):
        self.dial_min_area = new_value

    def run(self):
        while self.isRunning():
            if self.camera_flag is not None:
                self.resource = self.camera_flag.read()[1]
            self.loop()
            time.sleep(0.1)

    def stop(self):
        if self.camera_flag is not None:
            self.camera_flag.release()
            self.camera_flag = None
        self.resource = None
        self.save_flag = False
        self.terminate()

    def loop(self):
        if self.resource is None:
            return
        height, width, channel = self.resource.shape
        not_available =generate_na(self.resource)
        kernel = numpy.ones((5, 5))
        resource_gray = cv2.cvtColor(self.resource, cv2.COLOR_BGR2GRAY)

        if self.eq_hist:
            resource_gray = cv2.equalizeHist(resource_gray)

        gaussian = cv2.GaussianBlur(resource_gray,
                                    (2 * self.median_blur - 1, 2 * self.median_blur - 1),
                                    1)
        edges = cv2.Canny(gaussian, self.dial_thresh_x, self.dial_thresh_y)

        img_dilate = cv2.dilate(edges, kernel, iterations=2)
        img_erode = cv2.erode(img_dilate, kernel, iterations=1)

        contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)
        img_all_contours = cv2.drawContours(self.resource.copy(), contours, -1, (0, 255, 0), 10)
        drawn_polygon = self.resource.copy()

        poligon_points = self.find_biggest_poligon(contours)
        if poligon_points.size != 0:
            poligon_points = reorder(poligon_points)
            prev_contour = draw_rectangle(drawn_polygon, poligon_points, 5)
            pts1 = numpy.float32(poligon_points)
            pts2 = numpy.float32([[0, 0], [width, 0], [0, height], [width, height]])
            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            save_warp_colored = cv2.warpPerspective(self.resource, matrix, (width, height))

            # TO SAVE SECTION

            save_warp_gray = cv2.medianBlur(cv2.cvtColor(save_warp_colored, cv2.COLOR_BGR2GRAY),
                                            2 * self.median_blur - 1) if self.median_blur else cv2.cvtColor(
                save_warp_colored, cv2.COLOR_BGR2GRAY)

            img_adaptive_threshold = cv2.adaptiveThreshold(save_warp_gray, 255, 1, 1, 7, 2)

            img_adaptive_threshold = cv2.bitwise_not(img_adaptive_threshold)

            image_array = ([self.resource, edges, img_all_contours],
                           [prev_contour, save_warp_colored, img_adaptive_threshold])

            if self.save_flag and self.isRunning():
                save_key([save_warp_colored, img_adaptive_threshold], self.output)
            self.save_flag = False
        else:
            image_array = ([self.resource, edges, img_all_contours],
                           [not_available, not_available, not_available])

        stacked_images = self.stack_images(image_array, PREVIEW_TAGS)

        self.result.emit(stacked_images)

    def stack_images(self, imgs_list: tuple, list_lables: list = []):
        rows = len(imgs_list)
        cols = len(imgs_list[0])

        if isinstance(imgs_list[0], list):
            for x in range(0, rows):
                for y in range(0, cols):
                    if len(imgs_list[x][y].shape) == 2:
                        imgs_list[x][y] = cv2.cvtColor(imgs_list[x][y], cv2.COLOR_GRAY2BGR)

            if len(list_lables) != 0:
                for x in range(0, rows):
                    for y in range(0, cols):
                        imgs_list[x][y] = draw_on_image(imgs_list[x][y], list_lables[x][y], background=True)

            for i in range(0, rows):
                if i == 0:
                    final_img_stack = hor_stack_imgs(imgs_list[i])

                else:
                    final_img_stack = numpy.vstack((final_img_stack, hor_stack_imgs(imgs_list[i])))

            return final_img_stack

    def percent_of_resource_area(self, per) -> int:
        return int((per / 100) * (self.resource.shape[0] * self.resource.shape[1]))

    def find_biggest_poligon(self, contours):
        biggest = numpy.array([])
        for i in contours:
            area = cv2.contourArea(i)
            if self.percent_of_resource_area(self.dial_min_area) < area < self.percent_of_resource_area(
                    self.dial_max_area):
                peri = cv2.arcLength(i, True)
                approx = cv2.approxPolyDP(i, 0.02 * peri, True)
                if len(approx) == 4:
                    biggest = approx
        return biggest

    def rotate(self):
        if self.resource is not None:
            self.resource = cv2.rotate(self.resource, cv2.cv2.ROTATE_90_CLOCKWISE)

    def flip(self):
        if self.resource is not None:
            self.resource = cv2.flip(self.resource, 1)
