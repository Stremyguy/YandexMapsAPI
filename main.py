import os
import sys
import requests

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("data/main.ui", self)
        
        self.searchButton.clicked.connect(self.search)
        
        self.setup()
        self.search()
    
    def setup(self) -> None:
        self.scale_step = 5
        
        self.zoomSpinBox.setValue(20)
        self.zoomSpinBox.setSingleStep(self.scale_step)
        self.lat_lineEdit.setText("-96.839074")
        self.lon_lineEdit.setText("39.767235")
    
    def search(self) -> None:
        self.server_address = "https://static-maps.yandex.ru/v1?"
        self.api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.lat, self.lon, self.spn = self.lat_lineEdit.text(), self.lon_lineEdit.text(), self.zoomSpinBox.value()
        ll_spn = f"ll={self.lat},{self.lon}&spn={self.spn},{self.spn}"
        
        map_request = f"{self.server_address}{ll_spn}&apikey={self.api_key}"
        response = requests.get(map_request)
        
        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print(f"HTTP статус: {response.status_code} ({response.reason})")
            sys.exit(1)
        
        self.map_file = "map.png"
        
        with open(f"data/{self.map_file}", "wb") as file:
            file.write(response.content)
        
        self.pixmap = QPixmap(f"data/{self.map_file}")
        self.map_template.setPixmap(self.pixmap)
    
    def keyPressEvent(self, event: None) -> None:
        if event.key() == Qt.Key.Key_PageUp:
            self.zoomSpinBox.setValue(int(self.zoomSpinBox.value()) - self.scale_step)
        elif event.key() == Qt.Key.Key_PageDown:
            self.zoomSpinBox.setValue(int(self.zoomSpinBox.value()) + self.scale_step)

        self.search()
        
    def closeEvent(self, event: None) -> None:
        os.remove(f"data/{self.map_file}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_window = MainWindow()
    my_window.show()
    sys.exit(app.exec())
