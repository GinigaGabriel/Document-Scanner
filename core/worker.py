import time

from PyQt5.QtCore import QThread, pyqtSignal


class WorkerThread(QThread):
    result = pyqtSignal(object)
    resource=None



    def run(self):
        for i in range(0, 101, 10):
            time.sleep(2)
            self.result.emit(f"{i*self.resource}")
