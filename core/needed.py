import copy
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

WORKER = WorkerThread()


# icon_flip= QtGui.QPixmap("resources/flip.png")
# self.flip_source.setIcon(QtGui.QIcon(icon_flip))
# icon_rotate = QtGui.QPixmap("resources/rotate.png")
# self.rotate_source.setIcon(QtGui.QIcon(icon_rotate))

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

        # self.commands = (
        #     ('Generate Graphical User Interface', self.generate_gui()),
        #     ('Execute core functionality', self.loop()),
        #     ('Create signals between gui and controls ', self.create_signals())
        # )

    def detect_cameras(self):
        index = 0
        self.ui.source_camera.clear()
        self.ui.source_camera.setPlaceholderText('Cameras')
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            if not cap.read()[0]:
                break
            else:
                self.ui.source_camera.addItems([f'Camera {index + 1} \n {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}'
                                                f'x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}'])

            cap.release()
            index += 1

        if index == 0:
            self.ui.source_camera.setPlaceholderText('No cameras')

    def source_camera_value_changed(self):

        if self.ui.source_camera.currentIndex() != -1:
            if cv2.VideoCapture(self.ui.source_camera.currentIndex(), cv2.CAP_DSHOW).read()[0]:
                self.ui.source_dir.setEnabled(False)
                self.ui.source_file.setEnabled(False)
                self.ui.source_camera.setEnabled(False)
                self.ui.display_area.setText("Loading")
                WORKER.camera_flag = cv2.VideoCapture(self.ui.source_camera.currentIndex(), cv2.CAP_DSHOW)
                WORKER.camera_flag.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                WORKER.camera_flag.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                WORKER.start()
            else:
                QMessageBox(QMessageBox.Information, 'Camera not detected ',
                            'We will perform a quick scan for hardware changes',
                            buttons=QMessageBox.Ok).exec_()

                self.detect_cameras()

    def source_file_checked(self):
        path = self.get_image_path()
        if len(path):
            self.ui.source_dir.setEnabled(False)
            self.ui.source_camera.setEnabled(False)
            self.ui.previous_button.setVisible(False)
            self.ui.next_button.setVisible(False)
            WORKER.resource = copy.deepcopy(cv2.imread(path))
            WORKER.start()

    def source_dir_checked(self):
        self.ui.source_file.setChecked(False)
        self.ui.source_camera.setEnabled(False)

    def create_links(self):
        self.ui.output_path_label.setText('Desktop is default location.')  # move to gui.py
        self.ui.select_output_button.clicked.connect(self.select_output_dir)
        self.ui.source_dir.clicked.connect(self.source_dir_checked)
        self.ui.source_file.clicked.connect(self.source_file_checked)
        self.ui.clear_the_workspace.clicked.connect(self.clean_workspace)

        # UI Part
        self.ui.dial_thresh_x.valueChanged.connect(self.ui.lcd_thresh_x.display)
        self.ui.dial_thresh_y.valueChanged.connect(self.ui.lcd_thresh_y.display)
        self.ui.dial_min_area.valueChanged.connect(self.ui.lcd_min_area.display)
        self.ui.dial_max_area.valueChanged.connect(self.ui.lcd_max_area.display)
        self.ui.dial_kernel.valueChanged.connect(self.ui.lcd_kernel.display)
        self.ui.source_camera.currentIndexChanged.connect(self.source_camera_value_changed)

        self.detect_cameras()

        # Worker
        self.ui.flip_source.clicked.connect(WORKER.flip)
        self.ui.rotate_source.clicked.connect(WORKER.rotate)
        self.ui.eq_hist.clicked.connect(WORKER.set_eq_hist)
        self.ui.dial_thresh_x.valueChanged.connect(WORKER.set_dial_thresh_x)
        self.ui.dial_thresh_y.valueChanged.connect(WORKER.set_dial_thresh_y)
        self.ui.dial_kernel.valueChanged.connect(WORKER.set_kernel)
        self.ui.dial_min_area.valueChanged.connect(WORKER.set_dial_min_area)
        self.ui.dial_max_area.valueChanged.connect(WORKER.set_dial_max_area)

        WORKER.result.connect(self.show)

        sys.exit(self.app.exec_())

    def clean_workspace(self):
        try:
            if WORKER.isRunning():
                if self.messagebox_dialog('Clear the workspace', 'Are you sure ?'):
                    WORKER.stop()
                    LOGGER.info('The worker stopped')
                    self.ui.display_area.clear()
                    self.ui.source_dir.setEnabled(True)
                    self.ui.source_file.setEnabled(True)
                    self.ui.source_camera.setEnabled(True)
                    self.ui.source_camera.setCurrentIndex(-1)
                    self.ui.display_area.setText("Choose one of three options from top left corner. ")
                    LOGGER.info('The workspace has been cleaned')
        except Exception as e:
            print(e)

    def show(self, val):
        try:
            if WORKER.isRunning():
                stacked_images_copy = QtGui.QImage(val.data, val.shape[1], val.shape[0],
                                                   3 * val.shape[1],
                                                   QtGui.QImage.Format_BGR888)
                pixmap = QtGui.QPixmap(stacked_images_copy)
                self.ui.display_area.setPixmap(pixmap)
        except Exception as e:
            print(str(e))

    def get_image_path(self) -> str:
        return QFileDialog.getOpenFileName(self.main_window, "Open file", str(DESKTOP_PATH),
                                           'Image files (*.png *.jpg *.gif)')[0]

    def messagebox_dialog(self, title: str, text: str) -> bool:
        reply = QMessageBox.question(self.main_window, title, text,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        return False

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


# def loop(self, resource):
#
#     while True:
#         time.sleep(0.3)
#         height, width, channel = resource.shape
#         empty_img = numpy.zeros((height, width, channel), numpy.uint8)
#         kernel = numpy.ones((5, 5))
#         resource_gray = cv2.cvtColor(resource, cv2.COLOR_BGR2GRAY)
#
#         if self.ui.eq_hist.isChecked():
#             resource_gray = cv2.equalizeHist(resource_gray)
#
#         gaussian = cv2.GaussianBlur(resource_gray,
#                                     (2 * self.ui.dial_kernel.value() - 1, 2 * self.ui.dial_kernel.value() - 1),
#                                     1)
#         edges = cv2.Canny(gaussian, self.ui.dial_thresh_x.value(), self.ui.dial_thresh_y.value())
#
#         img_dilate = cv2.dilate(edges, kernel, iterations=2)
#         img_erode = cv2.erode(img_dilate, kernel, iterations=1)
#
#         contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_EXTERNAL,
#                                                cv2.CHAIN_APPROX_SIMPLE)
#         img_contours = resource.copy()
#         img_biggest_contour = resource.copy()
#         cv2.drawContours(img_contours, contours, -1, (170, 255, 0), 10)
#
#         biggest, max_area = self.find_biggest_contour(contours)
#         if biggest.size != 0:
#             biggest = self.reorder(biggest)
#             cv2.drawContours(img_biggest_contour, biggest, -1, (0, 255, 0), 20)
#             prev_contour = self.draw_rectangle(img_biggest_contour, biggest, 2)
#             pts1 = numpy.float32(biggest)
#             pts2 = numpy.float32([[0, 0], [width, 0], [0, height], [width, height]])
#             matrix = cv2.getPerspectiveTransform(pts1, pts2)
#             save_warp_colored = cv2.warpPerspective(resource, matrix, (width, height))
#
#             # TO SAVE SECTION
#
#             save_warp_gray = cv2.medianBlur(cv2.cvtColor(save_warp_colored, cv2.COLOR_BGR2GRAY),
#                                             2 * self.ui.dial_kernel.value() - 1) if self.ui.median_blur.isChecked() else cv2.cvtColor(
#                 save_warp_colored, cv2.COLOR_BGR2GRAY)
#
#             img_adaptive_threshold = cv2.adaptiveThreshold(save_warp_gray, 255, 1, 1, 7, 2)
#
#             img_adaptive_threshold = cv2.bitwise_not(img_adaptive_threshold)
#
#             image_array = ([resource, edges, prev_contour],
#                            [prev_contour, save_warp_colored,
#                             img_adaptive_threshold])
#
#         else:
#             image_array = ([resource, edges, prev_contour],
#                            [empty_img, empty_img, empty_img])
#
#         if cv2.waitKey(1):
#             find_key(cv2.waitKey(1))
#
#         stacked_images = self.stack_images(image_array, PREVIEW_TAGS)
#
#         stacked_images_copy = QtGui.QImage(stacked_images.data, stacked_images.shape[1], stacked_images.shape[0],
#                                            3 * stacked_images.shape[1],
#                                            QtGui.QImage.Format_RGB888)
#
#         pixmap = QtGui.QPixmap(stacked_images_copy)
#         self.ui.display_area.setPixmap(pixmap)
