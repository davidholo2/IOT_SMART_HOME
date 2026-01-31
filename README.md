Smart Warehouse IoT System - Wolt Market
A real-time IoT inventory management system designed for Wolt Market. The system monitors stock weights of fresh produce, automates restock orders via MQTT, and provides a cross-platform control dashboard (Desktop + Mobile).

🛠 Key Features
Live Inventory Simulation: Real-time weight tracking for 4 categories (Tomatoes, Cucumbers, Apples, Bananas).

Intelligent Auto-Reorder: Automated logistics trigger that sends refill requests when stock levels fall below 25kg.

Bidirectional MQTT Communication: Uses the HiveMQ broker to sync data between the edge device, backend manager, and mobile apps.

Persistence & Auditing: Every weight update and system event is logged into a CSV database for future audit.

Smart Filtering: Advanced logic to ignore legacy "retained" messages, ensuring the system only reacts to real-time commands.

📱 Mobile Integration (MQTT Dashboard)
This project supports remote monitoring and control through the MQTT Dashboard app (available on Android). This allows warehouse managers to track stock and trigger manual refills from anywhere.

How to Connect:
Broker Settings:

Server/Host: broker.hivemq.com

Port: 1883

Client ID: (Any unique string, e.g., Wolt_Mobile_123)

Monitoring Stock (Subscriber):

Add a Text or Display widget.

Topic: wolt/warehouse/smart_produce/inventory/sts.

This will display the live weight updates as they happen.

Manual Refill (Publisher):

Add a Button widget for each product.

Topic: wolt/warehouse/smart_produce/inventory/order.

Payload (Example): refill Tomatoes from iPhone (The system will identify the product and the source).

🚀 Getting Started
Requirements: Python 3.x, PyQt5, and paho-mqtt.

Run the Manager: Execute app_manager.py to start the backend logging and logic service.

Run the GUI: Execute inventory_gui.py to start the warehouse monitoring interface.

Connect: Click "CONNECT TO SERVER" on the GUI to begin live telemetry.

📂 Project Structure
inventory_gui.py: The main application containing UI logic, MQTT service, and inventory management classes.

app_manager.py: Backend service for processing system events and CSV logging.

inventory_log.csv: Persistent storage for all warehouse activities.
