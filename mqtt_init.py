import socket

# MQTT Broker Configuration
# Index 1 points to HiveMQ public broker
nb = 1
brokers = [str(socket.gethostbyname('vmm1.saaintertrade.com')),
           str(socket.gethostbyname('broker.hivemq.com'))]
ports = ['80', '1883']
broker_ip = brokers[nb]
port = ports[nb]

# MQTT Topic Hierarchy for Wolt Market
comm_topic = 'wolt/warehouse/smart_produce/'
topic_status = comm_topic + 'inventory/sts'    # For broadcasting stock levels
topic_order = comm_topic + 'inventory/order'     # For receiving refill commands

# Business Logic Thresholds (in KG)
LOW_STOCK_THRESHOLD = 30.0
AUTO_REORDER_THRESHOLD = 25.0
