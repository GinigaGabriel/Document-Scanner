import time
import numpy
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from ui.gui import *
from core.needed import *
from core.root import *

PREVIEW_TAGS = [["Original", "Threshold", "Contours"],
                ["Biggest Contour", "Warp Prespective", "Adaptive Threshold"]]


class WorkerThread(QThread):
    result = pyqtSignal(object)
    resource = None
    eq_hist = False
    i = 0

    def run(self):
        while self.resource is not None:
            self.loop()
            time.sleep(0.5)
            self.i += 1

        self.terminate()

    def save(self):
        print('test')

    def loop(self):
        try:

            height, width, channel = self.resource.shape
            empty_img = numpy.zeros((height, width, channel), numpy.uint8)
            kernel = numpy.ones((5, 5))
            resource_gray = cv2.cvtColor(self.resource, cv2.COLOR_BGR2GRAY)
            print(f'loop  {self.i}')

            # if self.eq_hist:
            #     resource_gray = cv2.equalizeHist(resource_gray)
            #
            # gaussian = cv2.GaussianBlur(resource_gray,
            #                             (2 * self.ui.dial_kernel.value() - 1, 2 * self.ui.dial_kernel.value() - 1),
            #                             1)
            # edges = cv2.Canny(gaussian, self.ui.dial_thresh_x.value(), self.ui.dial_thresh_y.value())
            #
            # img_dilate = cv2.dilate(edges, kernel, iterations=2)
            # img_erode = cv2.erode(img_dilate, kernel, iterations=1)
            #
            # contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_EXTERNAL,
            #                                        cv2.CHAIN_APPROX_SIMPLE)
            # img_contours = self.resource.copy()
            # img_biggest_contour = self.resource.copy()
            # cv2.drawContours(img_contours, contours, -1, (170, 255, 0), 10)
            #
            # biggest, max_area = self.find_biggest_contour(contours)
            # if biggest.size != 0:
            #     biggest = self.reorder(biggest)
            #     cv2.drawContours(img_biggest_contour, biggest, -1, (0, 255, 0), 20)
            #     prev_contour = self.draw_rectangle(img_biggest_contour, biggest, 2)
            #     pts1 = numpy.float32(biggest)
            #     pts2 = numpy.float32([[0, 0], [width, 0], [0, height], [width, height]])
            #     matrix = cv2.getPerspectiveTransform(pts1, pts2)
            #     save_warp_colored = cv2.warpPerspective(self.resource, matrix, (width, height))
            #
            #     # TO SAVE SECTION
            #
            #     save_warp_gray = cv2.medianBlur(cv2.cvtColor(save_warp_colored, cv2.COLOR_BGR2GRAY),
            #                                     2 * self.ui.dial_kernel.value() - 1) if self.ui.median_blur.isChecked() else cv2.cvtColor(
            #         save_warp_colored, cv2.COLOR_BGR2GRAY)
            #
            #     img_adaptive_threshold = cv2.adaptiveThreshold(save_warp_gray, 255, 1, 1, 7, 2)
            #
            #     img_adaptive_threshold = cv2.bitwise_not(img_adaptive_threshold)
            #
            #     image_array = ([self.resource, edges, prev_contour],
            #                    [prev_contour, save_warp_colored,
            #                     img_adaptive_threshold])
            #
            # else:
            #     image_array = ([self.resource, edges, img_contours],
            #                    [empty_img, empty_img, empty_img])

            # stacked_images = self.stack_images(image_array, PREVIEW_TAGS)
            try:
                self.result.emit(self.resource)
            except Exception as e:
                print(str(e))

        except Exception as e:
            print(str(e))

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
                        imgs_list[x][y] = self.draw_on_image(imgs_list[x][y], list_lables[x][y], background=True)

            for i in range(0, rows):
                if i == 0:
                    final_img_stack = self.hor_stack_imgs(imgs_list[i])

                else:
                    final_img_stack = numpy.vstack((final_img_stack, self.hor_stack_imgs(imgs_list[i])))

            return final_img_stack

    @staticmethod
    def draw_on_image(img, message, **kwargs):
        background = kwargs.get('background', False)

        if background:
            r_img = cv2.rectangle(img, (5, 5), (int(len(message) * 15 + 20), 50), (255, 255, 255), thickness=-1)

        r_img = cv2.putText(img, message, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

        return r_img

    def terminate(self) -> None:
        self.resource = None


    @staticmethod
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

    @staticmethod
    def hor_stack_imgs(list_of_imgs: list):
        horizontal_stack = None
        for x in range(0, len(list_of_imgs)):
            if x == 0:
                horizontal_stack = list_of_imgs[x]
            else:
                horizontal_stack = numpy.hstack((horizontal_stack, list_of_imgs[x]))

        return horizontal_stack

    @staticmethod
    def find_biggest_contour(contours):
        biggest = numpy.array([])
        max_area = 0
        for i in contours:
            area = cv2.contourArea(i)
            if area > 5000:
                peri = cv2.arcLength(i, True)
                approx = cv2.approxPolyDP(i, 0.02 * peri, True)
                if area > max_area and len(approx) == 4:
                    biggest = approx
                    max_area = area
        return biggest, max_area

    @staticmethod
    def draw_rectangle(img, biggest, thickness):
        cv2.line(img, (biggest[0][0][0], biggest[0][0][1]), (biggest[1][0][0], biggest[1][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[0][0][0], biggest[0][0][1]), (biggest[2][0][0], biggest[2][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[3][0][0], biggest[3][0][1]), (biggest[2][0][0], biggest[2][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[3][0][0], biggest[3][0][1]), (biggest[1][0][0], biggest[1][0][1]), (0, 255, 0),
                 thickness)

        return img

    def rotate(self):
        if self.resource is not None:
            self.resource = cv2.rotate(self.resource, cv2.cv2.ROTATE_90_CLOCKWISE)

    def flip(self):
        if self.resource is not None:
            self.resource = cv2.flip(self.resource, 1)
