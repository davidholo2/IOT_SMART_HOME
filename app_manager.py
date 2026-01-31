import paho.mqtt.client as mqtt
import time
import csv
import os
from datetime import datetime
from mqtt_init import *


def save_to_db(product, weight):
    file_exists = os.path.isfile('inventory_log.csv')
    with open('inventory_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Timestamp', 'Product', 'Weight_KG'])
        writer.writerow([datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"), product, weight])


def on_message(client, userdata, msg):
    m_decode = str(msg.payload.decode("utf-8", "ignore"))
    print(f"[*] Update: {m_decode}")

    if "Product:" in m_decode:
        try:
            parts = m_decode.split('|')
            product = parts[0].split(': ')[1].strip()
            weight = float(parts[1].split(': ')[1].strip())
            save_to_db(product, weight)  # Requirement 3d: DB Logging
        except:
            pass
    elif "refill" in m_decode:
        print(f"[ACTION LOGGED] {m_decode}")  # Requirement 3b: Process alerts


def main():
    client = mqtt.Client("Wolt_Inventory_Manager")
    client.on_message = on_message
    client.connect(broker_ip, int(port))
    client.subscribe(topic_status)
    client.subscribe(topic_order)
    client.loop_start()
    print("Manager ACTIVE - Logging all produce to CSV...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()


if __name__ == "__main__":
    main()
