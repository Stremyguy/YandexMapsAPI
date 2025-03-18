import os
import sys
import requests

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QPixmap


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("data/main.ui", self)
        
        self.searchButton.clicked.connect(self.search)
        
        self.setup()
        self.search()
    
    def setup(self) -> None:
        self.zoomSpinBox.setValue(21)
        self.lat_lineEdit.setText("-96.839074")
        self.lon_lineEdit.setText("39.767235")
    
    def search(self) -> None:
        server_address = "https://static-maps.yandex.ru/v1?"
        api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        lat, lon, spn = self.lat_lineEdit.text(), self.lon_lineEdit.text(), self.zoomSpinBox.value()
        ll_spn = f"ll={lat},{lon}&spn={spn},{spn}"
        
        map_request = f"{server_address}{ll_spn}&apikey={api_key}"
        response = requests.get(map_request)
        
        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print(f"HTTP статус: {response.status_code} ({response.reason})")
            sys.exit(1)
        
        self.map_file = "map.png"
        
        with open(f"data/tmp/{self.map_file}", "wb") as file:
            file.write(response.content)
        
        self.pixmap = QPixmap(f"data/tmp/{self.map_file}")
        self.map_template.setPixmap(self.pixmap)
    
    def closeEvent(self, event: None) -> None:
        os.remove(f"data/tmp/{self.map_file}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_window = MainWindow()
    my_window.show()
    sys.exit(app.exec())
