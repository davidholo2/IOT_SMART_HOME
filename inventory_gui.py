import sys
import random
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt

# --- CONFIGURATION SECTION ---
# Broker details - Using HiveMQ public broker
BROKER_URL = str(socket.gethostbyname('broker.hivemq.com'))
PORT = 1883
TOPIC_STATUS = 'wolt/warehouse/smart_produce/inventory/sts'
TOPIC_ORDER = 'wolt/warehouse/smart_produce/inventory/order'

# Business Logic Thresholds (in KG)
AUTO_REORDER_THRESHOLD = 25.0
LOW_STOCK_THRESHOLD = 30.0

# UI Styling
STYLE_SHEET = """
    QMainWindow { background-color: #1e1e2e; }
    QWidget#MainContent { background-color: #2b2b3b; border-radius: 15px; margin: 10px; }
    QLabel { color: #cdd6f4; font-size: 14px; font-family: 'Segoe UI'; }
    QComboBox { background-color: #181825; color: #fab387; border: 1px solid #45475a; border-radius: 5px; padding: 5px; }
    QLineEdit { background-color: #181825; color: #a6e3a1; border: 2px solid #45475a; border-radius: 8px; padding: 5px; font-size: 18px; font-weight: bold; }
    QPushButton#OrderBtn { background-color: #f38ba8; color: #11111b; border-radius: 10px; padding: 12px; font-weight: bold; }
    QPushButton#ServerBtn { background-color: #45475a; color: white; border-radius: 10px; padding: 8px; font-weight: bold; }
    QPushButton#AutoBtn { background-color: #313244; color: white; border-radius: 10px; padding: 8px; font-size: 11px; }
    QPushButton#AutoBtn:checked { background-color: #fab387; color: #11111b; }
    QTextEdit#AlertBox { background-color: #181825; color: #f38ba8; border-radius: 8px; font-size: 11px; font-family: 'Consolas'; }
"""


class InventoryManager:
    """Core logic for managing stock weights"""

    def __init__(self):
        self.stock = {"Tomatoes": 50.0, "Cucumbers": 40.0,
                      "Apples": 35.0, "Bananas": 30.0}
        self.active_orders = set()

    def simulate_consumption(self):
        """Simulates product weight decrease"""
        for product in self.stock:
            self.stock[product] -= random.uniform(0.3, 0.9)
            if self.stock[product] < 0:
                self.stock[product] = 0

    def add_weight(self, product, amount=25.0):
        if product in self.stock:
            self.stock[product] += amount
            if product in self.active_orders:
                self.active_orders.remove(product)
            return True
        return False


class WoltWarehouseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logic = InventoryManager()
        self.mqtt_client = None
        self.is_connected = False
        self.auto_mode = False

        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.execution_loop)
        self.timer.start(3000)

    def setup_ui(self):
        self.setWindowTitle('Wolt Market - Smart Inventory HQ')
        self.setFixedSize(450, 750)
        self.setStyleSheet(STYLE_SHEET)
        self.container = QWidget()
        self.container.setObjectName("MainContent")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("WOLT MARKET | SYSTEM CONNECTION"))
        self.btnServer = QPushButton("CONNECT TO SERVER")
        self.btnServer.setObjectName("ServerBtn")
        self.btnServer.clicked.connect(self.toggle_connection)
        layout.addWidget(self.btnServer)

        layout.addWidget(QLabel("MONITORING FOCUS:"))
        self.product_box = QComboBox()
        self.product_box.addItems(self.logic.stock.keys())
        self.product_box.currentIndexChanged.connect(self.update_display_only)
        layout.addWidget(self.product_box)

        self.weight_display = QLineEdit("OFFLINE")
        self.weight_display.setReadOnly(True)
        self.weight_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.weight_display)

        self.btnAuto = QPushButton("AUTO-REORDER: OFF")
        self.btnAuto.setObjectName("AutoBtn")
        self.btnAuto.setCheckable(True)
        self.btnAuto.clicked.connect(self.toggle_auto)
        layout.addWidget(self.btnAuto)

        self.btnOrder = QPushButton("MANUAL REFILL REQUEST")
        self.btnOrder.setObjectName("OrderBtn")
        self.btnOrder.clicked.connect(lambda: self.place_order(manual=True))
        layout.addWidget(self.btnOrder)

        layout.addWidget(QLabel("GLOBAL INVENTORY LOG:"))
        self.alert_box = QTextEdit()
        self.alert_box.setObjectName("AlertBox")
        self.alert_box.setReadOnly(True)
        layout.addWidget(self.alert_box)

        self.status_label = QLabel("STATUS: SYSTEM STANDBY")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.container.setLayout(layout)
        self.setCentralWidget(self.container)

    def toggle_connection(self):
        if not self.is_connected:
            cid = f"Wolt_Client_{random.randint(1000, 9999)}"
            self.mqtt_client = mqtt.Client(cid)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            try:
                self.mqtt_client.connect(BROKER_URL, PORT)
                self.mqtt_client.loop_start()
            except:
                self.add_alert("ERROR: Connection Failed.")
        else:
            self.is_connected = False
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.on_ui_disconnect()

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.mqtt_client.subscribe(TOPIC_ORDER)
            self.on_ui_connect()

    def on_mqtt_message(self, client, userdata, msg):
        if msg.retain:
            return  # Filter out old retained messages
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if "refill" in payload.lower():
            target_prod = self.product_box.currentText()
            for prod in self.logic.stock:
                if prod.lower() in payload.lower():
                    target_prod = prod
            self.add_alert(
                f"REMOTE ACTION: External refill request processed.")
            self.perform_refill(target_prod, "REMOTE")

    def on_ui_connect(self):
        self.btnServer.setText("DISCONNECT FROM SERVER")
        self.btnServer.setStyleSheet(
            "background-color: #a6e3a1; color: #11111b;")
        self.add_alert("SUCCESS: Cloud connection established.")

    def on_ui_disconnect(self):
        self.btnServer.setText("CONNECT TO SERVER")
        self.btnServer.setStyleSheet(
            "background-color: #45475a; color: white;")
        self.status_label.setText("STATUS: SYSTEM STANDBY")
        self.weight_display.setText("OFFLINE")
        self.add_alert("INFO: System is now Offline.")

    def update_display_only(self):
        if not self.is_connected:
            self.weight_display.setText("OFFLINE")
        else:
            current = self.product_box.currentText()
            self.weight_display.setText(f"{self.logic.stock[current]:.2f} kg")

    def toggle_auto(self):
        self.auto_mode = self.btnAuto.isChecked()
        self.btnAuto.setText(
            f"AUTO-REORDER: {'ON' if self.auto_mode else 'OFF'}")

    def execution_loop(self):
        # --- CRITICAL FIX: Block all logic and publishing if NOT connected ---
        if not self.is_connected or self.mqtt_client is None:
            return

        self.logic.simulate_consumption()
        for prod, weight in self.logic.stock.items():
            # Send live telemetry
            self.mqtt_client.publish(
                TOPIC_STATUS, f"Product: {prod} | Weight: {weight:.2f}")
            # Auto-reorder trigger
            if self.auto_mode and weight < AUTO_REORDER_THRESHOLD:
                if prod not in self.logic.active_orders:
                    self.add_alert(f"CRITICAL: {prod} low stock! Ordering...")
                    self.place_order(manual=False, product=prod)

        current = self.product_box.currentText()
        current_w = self.logic.stock[current]
        self.weight_display.setText(f"{current_w:.2f} kg")

        if current_w < AUTO_REORDER_THRESHOLD and self.auto_mode:
            self.status_label.setText(f"AUTO-ORDERING {current}...")
            self.status_label.setStyleSheet(
                "color: #fab387; font-weight: bold;")
        elif current_w < LOW_STOCK_THRESHOLD:
            self.status_label.setText(f"ALERT: Low stock on {current}!")
            self.status_label.setStyleSheet("color: #f38ba8;")
        else:
            self.status_label.setText("STATUS: MONITORING LIVE")
            self.status_label.setStyleSheet("color: #a6e3a1;")

    def place_order(self, manual=True, product=None):
        if not self.is_connected:
            return
        target = product if product else self.product_box.currentText()
        if target in self.logic.active_orders:
            return
        self.logic.active_orders.add(target)
        label = "MANUAL" if manual else "AUTO"
        self.mqtt_client.publish(TOPIC_ORDER, f"{label} refill for {target}")
        QTimer.singleShot(4000, lambda: self.perform_refill(target, label))

    def perform_refill(self, product, label):
        added = random.uniform(20, 30)
        if self.logic.add_weight(product, added):
            self.add_alert(
                f"SUCCESS: {product} restocked via {label} (+{added:.1f}kg)")

    def add_alert(self, text):
        self.alert_box.append(f"[{QTime.currentTime().toString()}] {text}")

    def closeEvent(self, event):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = WoltWarehouseApp()
    mainwin.show()
    sys.exit(app.exec_())
