import time
import numpy
import cv2
from PyQt5.QtCore import QThread, pyqtSignal

PREVIEW_TAGS = [["Original", "Threshold", "Contours"],
                ["Biggest Contour", "Warp Prespective", "Adaptive Threshold"]]


class WorkerThread(QThread):
    result = pyqtSignal(object)
    resource = None

    def run(self):
        if self.resource is not None:
            self.loop()
        time.sleep(0.2)

    def loop(self):
        while True:
            time.sleep(0.3)
            height, width, channel = self.resource.shape
            empty_img = numpy.zeros((height, width, channel), numpy.uint8)
            kernel = numpy.ones((5, 5))
            resource_gray = cv2.cvtColor(self.resource, cv2.COLOR_BGR2GRAY)

            if self.ui.eq_hist.isChecked():
                resource_gray = cv2.equalizeHist(resource_gray)

            gaussian = cv2.GaussianBlur(resource_gray,
                                        (2 * self.ui.dial_kernel.value() - 1, 2 * self.ui.dial_kernel.value() - 1),
                                        1)
            edges = cv2.Canny(gaussian, self.ui.dial_thresh_x.value(), self.ui.dial_thresh_y.value())

            img_dilate = cv2.dilate(edges, kernel, iterations=2)
            img_erode = cv2.erode(img_dilate, kernel, iterations=1)

            contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)
            img_contours = self.resource.copy()
            img_biggest_contour = self.resource.copy()
            cv2.drawContours(img_contours, contours, -1, (170, 255, 0), 10)

            biggest, max_area = self.find_biggest_contour(contours)
            if biggest.size != 0:
                biggest = self.reorder(biggest)
                cv2.drawContours(img_biggest_contour, biggest, -1, (0, 255, 0), 20)
                prev_contour = self.draw_rectangle(img_biggest_contour, biggest, 2)
                pts1 = numpy.float32(biggest)
                pts2 = numpy.float32([[0, 0], [width, 0], [0, height], [width, height]])
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                save_warp_colored = cv2.warpPerspective(self.resource, matrix, (width, height))

                # TO SAVE SECTION

                save_warp_gray = cv2.medianBlur(cv2.cvtColor(save_warp_colored, cv2.COLOR_BGR2GRAY),
                                                2 * self.ui.dial_kernel.value() - 1) if self.ui.median_blur.isChecked() else cv2.cvtColor(
                    save_warp_colored, cv2.COLOR_BGR2GRAY)

                img_adaptive_threshold = cv2.adaptiveThreshold(save_warp_gray, 255, 1, 1, 7, 2)

                img_adaptive_threshold = cv2.bitwise_not(img_adaptive_threshold)

                image_array = ([self.resource, edges, prev_contour],
                               [prev_contour, save_warp_colored,
                                img_adaptive_threshold])

            else:
                image_array = ([self.resource, edges, img_contours],
                               [empty_img, empty_img, empty_img])

            stacked_images = self.stack_images(image_array, PREVIEW_TAGS)
            self.result.emit(stacked_images)
