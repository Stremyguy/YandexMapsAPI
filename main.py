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
        self.scale_step = 1
        self.move_step = 0.1
        self.min_lon = -180.0
        self.max_lon = 180.0
        self.min_lat = -85.0
        self.max_lat = 85.0

        self.zoomSpinBox.setRange(1, 20)
        self.zoomSpinBox.setValue(10)
        self.zoomSpinBox.setSingleStep(self.scale_step)
        
        self.lon_lineEdit.setText("-96.839074")
        self.lat_lineEdit.setText("39.767235")
    
    def search(self) -> None:
        self.server_address = "https://static-maps.yandex.ru/v1?"
        self.api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        
        try:
            lon = float(self.lon_lineEdit.text())
            lat = float(self.lat_lineEdit.text())
            zoom = float(self.zoomSpinBox.value())
        except ValueError:
            print("Неверные координаты или параметр масштабирования")
            return
        
        spn = 20.0 / zoom 
        
        spn = max(0.001, min(spn, 90.0))
        
        ll_spn = f"ll={lon},{lat}&spn={spn},{spn}"
        map_request = f"{self.server_address}{ll_spn}&apikey={self.api_key}"
        
        response = requests.get(map_request)
        
        if not response.ok:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print(f"HTTP статус: {response.status_code} ({response.reason})")
            print(f"Response: {response.text}")
            return
        
        self.map_file = "map.png"
        map_path = f"data/{self.map_file}"
        
        try:
            with open(map_path, "wb") as file:
                file.write(response.content)
            
            self.pixmap = QPixmap(map_path)
            self.map_template.setPixmap(self.pixmap)
        except Exception as e:
            print(f"Ошибка при загрузке карты: {e}")
    
    def keyPressEvent(self, event: None) -> None:
        if event.key() == Qt.Key.Key_PageUp:
            new_zoom = self.zoomSpinBox.value() - self.scale_step
            self.zoomSpinBox.setValue(max(1, new_zoom))
        elif event.key() == Qt.Key.Key_PageDown:
            new_zoom = self.zoomSpinBox.value() + self.scale_step
            self.zoomSpinBox.setValue(min(20, new_zoom))
        
        try:
            lon = float(self.lon_lineEdit.text())
            lat = float(self.lat_lineEdit.text())
        except ValueError:
            return
        
        move_step = self.move_step * (10 / self.zoomSpinBox.value())
        
        if event.key() == Qt.Key.Key_Up:
            lat += move_step
            lat = min(lat, self.max_lat)
        elif event.key() == Qt.Key.Key_Down:
            lat -= move_step
            lat = max(lat, self.min_lat)
        elif event.key() == Qt.Key.Key_Right:
            lon += move_step
            if lon > self.max_lon:
                lon = self.min_lon + (lon - self.max_lon)
        elif event.key() == Qt.Key.Key_Left:
            lon -= move_step
            if lon < self.min_lon:
                lon = self.max_lon - (self.min_lon - lon)
        
        self.lon_lineEdit.setText(f"{lon:.6f}")
        self.lat_lineEdit.setText(f"{lat:.6f}")
        
        self.search()
        
    def closeEvent(self, event: None) -> None:
        if hasattr(self, "map_file"):
            try:
                os.remove(f"data/{self.map_file}")
            except (FileNotFoundError, PermissionError) as e:
                print(f"Ошибка: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_window = MainWindow()
    my_window.show()
    sys.exit(app.exec())