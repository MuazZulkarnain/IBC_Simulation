#!/usr/bin/env python3

import sys
import threading
import socket
import time
import os

class HubNode:
    def __init__(self, node_name):
        self.node_name = node_name
        self.balances = {}  # Token balances for each zone
        self.listen_port = 8000
        self.zone_relayers = {}  # Mapping of zones to relayer IPs

        # Initialize relayer IPs for each zone (adjust IPs as needed)
        self.zone_relayers = {
            'A': '10.0.0.10',  # Relayer A IP on Hub network
            'B': '10.0.0.11',  # Relayer B IP on Hub network
            'C': '10.0.0.12',  # Relayer C IP on Hub network
        }

        # Set up logging
        self.logs_dir = '/home/ubuntu/IBC_Simulation/mininet_shared/logs'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        self.log_file = os.path.join(self.logs_dir, f'{self.node_name}_transfer_log.txt')
        self.log('Hub node initialized.')

    def log(self, message):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} {message}\n")
        print(f"{timestamp} {message}")

    def start(self):
        threading.Thread(target=self.ibc_listener, daemon=True).start()
        self.run_node()

    def run_node(self):
        while True:
            self.log("Running Hub node.")
            time.sleep(10)

    def ibc_listener(self):
        # Listen for IBC messages from relayers
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', self.listen_port))
            s.listen()
            self.log(f"Listening for IBC messages on port {self.listen_port}")
            while True:
                conn, addr = s.accept()
                data = conn.recv(1024)
                if data:
                    message = data.decode()
                    self.log(f"Received IBC message: {message} from {addr}")
                    self.handle_ibc_message(message)

    def handle_ibc_message(self, message):
        # Simplified message handling
        if message.startswith('IBC_TRANSFER'):
            # Message format: 'IBC_TRANSFER,<amount>,<sender_zone>,<sender>,<destination_zone>,<transaction_id>'
            parts = message.strip().split(',')
            if len(parts) == 6:
                _, amount_str, sender_zone, sender, destination_zone, transaction_id = parts
                amount = int(amount_str)

                # Update balances (for simulation purposes)
                self.balances[sender_zone] = self.balances.get(sender_zone, 0) - amount
                self.balances[destination_zone] = self.balances.get(destination_zone, 0) + amount

                self.log(f"Processed transfer {transaction_id} of {amount} tokens from Zone {sender_zone} to Zone {destination_zone}.")
                self.log(f"Balances: {self.balances}")

                # Forward the IBC message to the destination zone via its relayer
                self.forward_to_zone(message, destination_zone)
            else:
                self.log(f"Malformed IBC_TRANSFER message: {message}")
        else:
            self.log(f"Unknown message type: {message}")

    def forward_to_zone(self, message, zone_label):
        # Forward the IBC message to the destination zone's relayer
        relayer_ip = self.zone_relayers.get(zone_label)
        if relayer_ip:
            port = 8000
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((relayer_ip, port))
                    s.sendall(message.encode())
                    self.log(f"Forwarded IBC packet to relayer for Zone {zone_label}")
            except Exception as e:
                self.log(f"Error forwarding to Zone {zone_label}'s relayer: {e}")
        else:
            self.log(f"No relayer found for Zone {zone_label}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 hub_node.py <node_name>")
        sys.exit(1)
    node = HubNode(sys.argv[1])
    node.start()