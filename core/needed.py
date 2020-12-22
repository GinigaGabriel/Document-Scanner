import pathlib
import abc
import cv2
import numpy
import sys
from core.key_shortcuts import find_key
from core.worker import *
import logging
import threading
from ui.gui import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem
import time
from PyQt5.QtWidgets import QFileDialog

LOGGER = logging.getLogger('root')
DESKTOP_PATH = pathlib.Path.home() / 'Desktop'
PREVIEW_TAGS = [["Original", "Threshold", "Contours"],
                ["Biggest Contour", "Warp Prespective", "Adaptive Threshold"]]



class Resources(abc.ABC):
    pass


class Backend(Resources):

    def __init__(self):
        self.output_dir = pathlib.Path.home() / 'Desktop' / 'DS'
        self.output_dir.parent.mkdir(parents=True, exist_ok=True)
        self.app = QtWidgets.QApplication(sys.argv)
        self.ui = Ui_MainWindow()
        self.main_window = QtWidgets.QMainWindow()

        self.ui.setupUi(self.main_window)

        self.main_window.show()
        self.test=WorkerThread()



    def catch(self,val):
        print(val)

        # self.commands = (
        #     ('Generate Graphical User Interface', self.generate_gui()),
        #     ('Execute core functionality', self.loop()),
        #     ('Create signals between gui and controls ', self.create_signals())
        # )

    def detect_cameras(self):
        index = 0
        self.ui.souce_camera.clear()
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.read()[0]:
                break
            else:
                self.ui.souce_camera.addItems([f'Camera {index + 1}'])
            cap.release()
            index += 1

    def messagebox_dialog(self, title: str, text: str) -> bool:
        reply = QMessageBox.question(self.main_window, title, text,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        return False

    def source_camera_checked(self):
        self.ui.source_dir.setChecked(False)
        self.ui.source_file.setChecked(False)

    def source_file_checked(self):
        path = self.get_image_path()
        if len(path):
            self.ui.source_dir.setChecked(False)
            self.ui.souce_camera.setEnabled(False)
            self.ui.previous_button.setVisible(False)
            self.ui.next_button.setVisible(False)
            self.test.resource=3.6
            self.test.start()


    def loop(self, resource):
        print(type(resource))
        print(resource)
        while True:
            time.sleep(0.3)
            height, width, channel = resource.shape
            empty_img = numpy.zeros((height, width, channel), numpy.uint8)
            kernel = numpy.ones((5, 5))
            resource_gray = cv2.cvtColor(resource, cv2.COLOR_BGR2GRAY)

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
            img_contours = resource.copy()
            img_biggest_contour = resource.copy()
            cv2.drawContours(img_contours, contours, -1, (170, 255, 0), 10)

            biggest, max_area = self.find_biggest_contour(contours)
            if biggest.size != 0:
                biggest = self.reorder(biggest)
                cv2.drawContours(img_biggest_contour, biggest, -1, (0, 255, 0), 20)
                prev_contour = self.draw_rectangle(img_biggest_contour, biggest, 2)
                pts1 = numpy.float32(biggest)
                pts2 = numpy.float32([[0, 0], [width, 0], [0, height], [width, height]])
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                save_warp_colored = cv2.warpPerspective(resource, matrix, (width, height))

                # TO SAVE SECTION

                save_warp_gray = cv2.medianBlur(cv2.cvtColor(save_warp_colored, cv2.COLOR_BGR2GRAY),
                                                2 * self.ui.dial_kernel.value() - 1) if self.ui.median_blur.isChecked() else cv2.cvtColor(
                    save_warp_colored, cv2.COLOR_BGR2GRAY)

                img_adaptive_threshold = cv2.adaptiveThreshold(save_warp_gray, 255, 1, 1, 7, 2)

                img_adaptive_threshold = cv2.bitwise_not(img_adaptive_threshold)

                image_array = ([resource, edges, prev_contour],
                               [prev_contour, save_warp_colored,
                                img_adaptive_threshold])

            else:
                image_array = ([resource, edges, prev_contour],
                               [empty_img, empty_img, empty_img])

            if cv2.waitKey(1):
                find_key(cv2.waitKey(1))

            stacked_images = self.stack_images(image_array, PREVIEW_TAGS)

            stacked_images_copy = QtGui.QImage(stacked_images.data, stacked_images.shape[1], stacked_images.shape[0],
                                               3 * stacked_images.shape[1],
                                               QtGui.QImage.Format_RGB888)

            pixmap = QtGui.QPixmap(stacked_images_copy)
            self.ui.display_area.setPixmap(pixmap)

    def source_dir_checked(self):
        self.ui.source_file.setChecked(False)
        self.ui.souce_camera.setEnabled(False)

    def get_image_path(self) -> str:
        return QFileDialog.getOpenFileName(self.main_window, "Open file", str(DESKTOP_PATH),
                                           'Image files (*.png *.jpg *.gif)')[0]

    def select_output_dir(self):
        directory = str(QFileDialog.getExistingDirectory(self.main_window, "Select Directory"))
        if pathlib.Path(directory).is_dir() and len(directory) > 3:
            self.output_dir = pathlib.Path(directory)
            lenght_of_path = len(str(self.output_dir))
            self.ui.output_path_label.setToolTip(str(directory))
            if lenght_of_path > 40:
                self.ui.output_path_label.setText("..." + str(self.output_dir)[lenght_of_path - 40:lenght_of_path])
            else:
                self.ui.output_path_label.setText(str(self.output_dir))

    def create_signals(self):
        self.ui.output_path_label.setText('Desktop is default location.')
        self.ui.select_output_button.clicked.connect(self.select_output_dir)
        self.ui.source_dir.clicked.connect(self.source_dir_checked)
        self.ui.source_file.clicked.connect(self.source_file_checked)
        self.ui.clear_the_workspace.clicked.connect(self.clean_workspace)
        self.ui.souce_camera.setPlaceholderText('Cameras')
        self.ui.dial_thresh_x.valueChanged.connect(self.ui.lcd_thresh_x.display)
        self.detect_cameras()

        self.test.result.connect(self.catch)

        self.ui.dial_thresh_y.valueChanged.connect(self.ui.lcd_thresh_y.display)
        self.ui.dial_kernel.valueChanged.connect(self.ui.lcd_kernel.display)

        sys.exit(self.app.exec_())

    def clean_workspace(self):
        if self.messagebox_dialog('Clear the workspace', 'Are you sure ?'):
            if self.thread_file.is_alive():
                print('dadsa')
                self.thread_file.join()
            self.ui.display_area.clear()
            self.ui.source_file.setEnabled(True)
            self.ui.souce_camera.setEnabled(True)
            self.ui.source_dir.setEnabled(True)
            LOGGER.info('The workspace has been cleaned')

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
                    final_img_stack = self.hstack_imgs(imgs_list[i])

                else:
                    final_img_stack = numpy.vstack((final_img_stack, self.hstack_imgs(imgs_list[i])))

            return final_img_stack

    def reorder(self, myPoints):
        myPoints = myPoints.reshape((4, 2))
        myPointsNew = numpy.zeros((4, 1, 2), dtype=numpy.int32)
        add = myPoints.sum(1)

        myPointsNew[0] = myPoints[numpy.argmin(add)]
        myPointsNew[3] = myPoints[numpy.argmax(add)]
        diff = numpy.diff(myPoints, axis=1)
        myPointsNew[1] = myPoints[numpy.argmin(diff)]
        myPointsNew[2] = myPoints[numpy.argmax(diff)]

        return myPointsNew

    @staticmethod
    def find_biggest_contour( contours):
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
    def draw_rectangle( img, biggest, thickness):
        cv2.line(img, (biggest[0][0][0], biggest[0][0][1]), (biggest[1][0][0], biggest[1][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[0][0][0], biggest[0][0][1]), (biggest[2][0][0], biggest[2][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[3][0][0], biggest[3][0][1]), (biggest[2][0][0], biggest[2][0][1]), (0, 255, 0),
                 thickness)
        cv2.line(img, (biggest[3][0][0], biggest[3][0][1]), (biggest[1][0][0], biggest[1][0][1]), (0, 255, 0),
                 thickness)

        return img

    @staticmethod
    def draw_on_image(img, message, **kwargs):
        background = kwargs.get('background', False)

        if background:
            r_img = cv2.rectangle(img, (5, 5), (int(len(message) * 15 + 20), 50), (255, 255, 255), thickness=-1)

        r_img = cv2.putText(img, message, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

        return r_img

    @staticmethod
    def hstack_imgs(list_of_imgs: list):
        hstack = None
        for x in range(0, len(list_of_imgs)):
            if x == 0:
                hstack = list_of_imgs[x]
            else:
                hstack = numpy.hstack((hstack, list_of_imgs[x]))
        return hstack

# def find_key(k):
#     if k == 'a':
#
#     elif x == 'b':
#
#     if x in 'bc':
#
#     elif x in 'xyz':
#
#     else:

## if cv2.waitKey(1):
#     find_key(cv2.waitKey(1))
