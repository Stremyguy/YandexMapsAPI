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
        self.theme_comboBox.currentTextChanged.connect(self.toggle_theme)

        self.searchButton_2.clicked.connect(self.search_object)
        self.object_lineEdit.returnPressed.connect(self.search_object)
        self.resetButton.clicked.connect(self.reset_search)
        self.postalCode_checkBox.stateChanged.connect(self.search_object)
        
        self.map_template.setMouseTracking(True)
        
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
        
        self.current_theme = "light"
        self.current_marker = None
        self.current_address = ""
    
    def toggle_theme(self) -> None:
        theme = self.theme_comboBox.currentText()
        self.current_theme = "dark" if theme == "Темная" else "light"
        self.search()
    
    def reset_search(self) -> None:
        self.current_marker = None
        self.current_address = ""
        self.addressLine.setText("")
        self.search()
    
    def mousePressEvent(self, event: None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.map_template.mapFrom(self, event.pos())
            if self.map_template.rect().contains(pos):
                self.handle_left_click(pos)
        elif event.button() == Qt.MouseButton.RightButton:
            pos = self.map_template.mapFrom(self, event.pos())
            if self.map_template.rect().contains(pos):
                self.handle_right_click(pos)
    
    def handle_left_click(self, pos: None) -> None:
        try:
            lon = float(self.lon_lineEdit.text())
            lat = float(self.lat_lineEdit.text())
            zoom = float(self.zoomSpinBox.value())
        except ValueError:
            return
        
        width = self.map_template.width()
        height = self.map_template.height()
        
        spn = 20.0 / zoom
        lon_per_pixel = spn * 2 / width
        lat_per_pixel = spn * 2 / height
        
        click_x = pos.x()
        click_y = pos.y()
        
        center_x = width / 2
        center_y = height / 2
        
        delta_lon = (click_x - center_x) * lon_per_pixel
        delta_lat = (center_y - click_y) * lat_per_pixel
        
        click_lon = lon + delta_lon
        click_lat = lat + delta_lat
        
        self.lon_lineEdit.setText(f"{click_lon:.6f}")
        self.lat_lineEdit.setText(f"{click_lat:.6f}")
        
        self.current_marker = (click_lon, click_lat)
        self.search_object_by_coords(click_lon, click_lat)
    
    def handle_right_click(self, pos: None) -> None:
        try:
            lon = float(self.lon_lineEdit.text())
            lat = float(self.lat_lineEdit.text())
            zoom = float(self.zoomSpinBox.value())
        except ValueError:
            return

        width = self.map_template.width()
        height = self.map_template.height()
        
        spn = 20.0 / zoom
        lon_per_pixel = spn * 2 / width
        lat_per_pixel = spn * 2 / height

        click_x = pos.x()
        click_y = pos.y()
        
        center_x = width / 2
        center_y = height / 2
        
        delta_lon = (click_x - center_x) * lon_per_pixel
        delta_lat = (center_y - click_y) * lat_per_pixel
        
        click_lon = lon + delta_lon
        click_lat = lat + delta_lat

        self.search_organization(click_lon, click_lat)
    
    def search_organization(self, lon: float, lat: float) -> None:
        search_api_server = "https://search-maps.yandex.ru/v1/"
        api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
        
        search_params = {
            "apikey": api_key,
            "text": "",
            "lang": "ru_RU",
            "ll": f"{lon},{lat}",
            "spn": "0.0005,0.0005",
            "type": "biz",
            "results": 1
        }
        
        try:
            response = requests.get(search_api_server, params=search_params)
            if response.ok:
                data = response.json()
                if data.get("features"):
                    organization = data["features"][0]
                    org_name = organization["properties"]["CompanyMetaData"]["name"]
                    org_address = organization["properties"]["CompanyMetaData"]["address"]
                    
                    org_pos = organization["geometry"]["coordinates"]
                    org_lon, org_lat = org_pos[0], org_pos[1]

                    distance = ((org_lon - lon) ** 2 + (org_lat - lat) ** 2) ** 0.5 * 111320
                    
                    if distance <= 50:
                        self.current_marker = (org_lon, org_lat)
                        self.current_address = f"{org_name}, {org_address}"
                        self.addressLine.setText(self.current_address)
                        self.search()
                    else:
                        self.reset_search()
                else:
                    self.reset_search()
        except Exception as e:
            print(f"Ошибка поиска организации: {e}")
            self.reset_search()
    
    def search_object_by_coords(self, lon: float, lat: float) -> None:
        geocoder_api = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "geocode": f"{lon},{lat}",
            "format": "json"
        }
        
        try:
            response = requests.get(geocoder_api, params=params)
            if response.ok:
                data = response.json()
                
                feature = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                self.current_address = feature["metaDataProperty"]["GeocoderMetaData"]["text"]
                
                if self.postalCode_checkBox.isChecked():
                    postal_code = feature["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code", "")
                    if postal_code:
                        self.current_address = f"{postal_code}, {self.current_address}"
                
                self.addressLine.setText(self.current_address)
                self.search()
        except Exception as e:
            print(f"Ошибка геокодирования: {e}")
    
    def search_object(self) -> None:
        search_text = self.object_lineEdit.text().strip()
        if not search_text:
            return
        
        print(search_text)
        
        geocoder_api = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "geocode": search_text,
            "format": "json"
        }
        
        try:
            response = requests.get(geocoder_api, params=params)
            if response.ok:
                data = response.json()
                
                feature = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                pos = feature["Point"]["pos"]
                lon, lat = map(float, pos.split())
                
                self.current_address = feature["metaDataProperty"]["GeocoderMetaData"]["text"]
                
                if self.postalCode_checkBox.isChecked():
                    postal_code = feature["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                    if postal_code:
                        self.current_address = f"{postal_code}, {self.current_address}"
                
                self.lon_lineEdit.setText(f"{lon:.6f}")
                self.lat_lineEdit.setText(f"{lat:.6f}")
                self.addressLine.setText(self.current_address)
                self.current_marker = (lon, lat)
                self.search()
        except Exception as e:
            print(f"Ошибка геокодирования: {e}")
    
    def search(self) -> None:
        try:
            lon = float(self.lon_lineEdit.text())
            lat = float(self.lat_lineEdit.text())
            zoom = float(self.zoomSpinBox.value())
        except ValueError:
            print("Неверные координаты или параметр масштабирования")
            return
        
        spn = 20.0 / zoom 
        spn = max(0.001, min(spn, 90.0))
        
        params = {
            "ll": f"{lon},{lat}",
            "spn": f"{spn},{spn}",
            "apikey": "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13",
            "l": "map",
        }
        
        if self.current_theme == "dark":
            params["theme"] = "dark"
        
        if self.current_marker:
            marker_lon, marker_lat = self.current_marker
            params["pt"] = f"{marker_lon},{marker_lat},pm2blm"
        
        response = requests.get("https://static-maps.yandex.ru/1.x/", params=params)
        
        if not response.ok:
            print("Ошибка выполнения запроса:")
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
