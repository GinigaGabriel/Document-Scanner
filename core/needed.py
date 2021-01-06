from core.worker import *
from ui.gui import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem
import pathlib
import sys
import copy
from PyQt5.QtWidgets import QFileDialog
import logging


DESKTOP_PATH = pathlib.Path.home() / 'Desktop'

WORKER = WorkerThread()

LOGGER=logging.getLogger(__name__)

# icon_flip= QtGui.QPixmap("resources/flip.png")
# self.flip_source.setIcon(QtGui.QIcon(icon_flip))
# icon_rotate = QtGui.QPixmap("resources/rotate.png")
# self.rotate_source.setIcon(QtGui.QIcon(icon_rotate))

class Backend():

    def __init__(self):

        self.output_dir = pathlib.Path.home() / 'Desktop' / 'DS'
        self.output_dir.parent.mkdir(parents=True, exist_ok=True)
        self.app = QtWidgets.QApplication(sys.argv)
        self.ui = Ui_MainWindow()
        self.main_window = QtWidgets.QMainWindow()

        self.ui.setupUi(self.main_window)

        self.main_window.show()

        self.commands = (
            ('Detect cameras', self.detect_cameras()),
            ('Create signals between gui and controls ', self.create_links()),
            ('Prepare environment', self.create_output_dir())
        )

    def create_output_dir(self):
        self.output_dir.parent.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'Colored').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'Binary').mkdir(parents=True, exist_ok=True)

    def detect_cameras(self):
        index = 0
        self.ui.source_camera.clear()
        LOGGER.info('camera')
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
            self.ui.source_camera.setEnabled(False)

    def source_camera_value_changed(self):
        if self.ui.source_camera.currentIndex() != -1:
            if cv2.VideoCapture(self.ui.source_camera.currentIndex(), cv2.CAP_DSHOW).read()[0]:
                self.ui.source_file.setEnabled(False)
                self.ui.source_camera.setEnabled(False)
                self.ui.display_area.setText("Loading")
                WORKER.camera_flag = cv2.VideoCapture(self.ui.source_camera.currentIndex(), cv2.CAP_DSHOW)
                WORKER.camera_flag.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                WORKER.camera_flag.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                WORKER.start()
            else:
                QMessageBox(QMessageBox.Information, 'Camera not detected ',
                            'We will perform a quick scan for hardware changes', buttons=QMessageBox.Ok).exec_()
                self.detect_cameras()

    def source_file_checked(self):
        path = self.get_image_path()
        if len(path):
            self.ui.source_camera.setEnabled(False)
            self.ui.previous_button.setVisible(False)
            self.ui.next_button.setVisible(False)
            WORKER.resource = copy.deepcopy(cv2.imread(path))
            WORKER.start()

    def create_links(self):
        self.ui.output_path_label.setText('Desktop is default location.')  # move to gui.py
        self.ui.select_output_button.clicked.connect(self.select_output_dir)
        self.ui.source_file.clicked.connect(self.source_file_checked)
        self.ui.clear_the_workspace.clicked.connect(self.clean_workspace)

        # UI Part
        self.ui.dial_thresh_x.valueChanged.connect(self.ui.lcd_thresh_x.display)
        self.ui.dial_thresh_y.valueChanged.connect(self.ui.lcd_thresh_y.display)
        self.ui.dial_min_area.valueChanged.connect(self.ui.lcd_min_area.display)
        self.ui.dial_max_area.valueChanged.connect(self.ui.lcd_max_area.display)
        self.ui.dial_median.valueChanged.connect(self.ui.lcd_median.display)
        self.ui.dial_filter_dots.valueChanged.connect(self.ui.lcd_filter_dots.display)
        self.ui.source_camera.currentIndexChanged.connect(self.source_camera_value_changed)
        self.detect_cameras()

        # Worker
        self.ui.save_button.clicked.connect(WORKER.set_save_flag)
        self.ui.flip_source.clicked.connect(WORKER.flip)
        self.ui.rotate_source.clicked.connect(WORKER.rotate)
        self.ui.eq_hist.clicked.connect(WORKER.set_eq_hist)
        self.ui.dial_thresh_x.valueChanged.connect(WORKER.set_dial_thresh_x)
        self.ui.dial_thresh_y.valueChanged.connect(WORKER.set_dial_thresh_y)
        self.ui.dial_median.valueChanged.connect(WORKER.set_kernel)
        self.ui.dial_min_area.valueChanged.connect(WORKER.set_dial_min_area)
        self.ui.dial_max_area.valueChanged.connect(WORKER.set_dial_max_area)
        self.ui.dial_filter_dots.valueChanged.connect(WORKER.set_dial_filter_dots)
        WORKER.output = self.output_dir
        WORKER.result.connect(self.show)

        sys.exit(self.app.exec_())

    def clean_workspace(self):
        if WORKER.isRunning():
            if self.messagebox_dialog('Clear the workspace', 'Are you sure ?'):
                WORKER.stop()
                LOGGER.info('The worker stopped')
                self.ui.display_area.clear()
                self.ui.source_file.setEnabled(True)
                self.ui.source_camera.setEnabled(True)
                self.ui.source_camera.setCurrentIndex(-1)
                self.ui.display_area.setText("Choose one of two options from top left corner. ")
                LOGGER.info('The workspace has been cleaned')

    def show(self, val):
        if WORKER.isRunning():
            stacked_images_copy = QtGui.QImage(val.data, val.shape[1], val.shape[0],
                                               3 * val.shape[1], QtGui.QImage.Format_BGR888)
            pixmap = QtGui.QPixmap(stacked_images_copy)
            self.ui.display_area.setPixmap(pixmap)

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
            self.output_dir.parent.mkdir(parents=True, exist_ok=True)
            WORKER.output = pathlib.Path(directory)
            lenght_of_path = len(str(self.output_dir))
            self.ui.output_path_label.setToolTip(str(directory))
            if lenght_of_path > 40:
                self.ui.output_path_label.setText("..." + str(self.output_dir)[lenght_of_path - 40:lenght_of_path])
            else:
                self.ui.output_path_label.setText(str(self.output_dir))
