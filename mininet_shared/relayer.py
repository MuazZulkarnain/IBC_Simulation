#!/usr/bin/env python3

import sys
import threading
import socket
import time
import os

class Relayer:
    def __init__(self, node_name, zone_label):
        self.node_name = node_name
        self.zone_label = zone_label
        self.hub_ip = f'10.0.0.{10 + ord(zone_label) - ord("A")}'
        self.zone_ip = f'10.0.{ord(zone_label) - ord("A") + 1}.10'
        self.listen_port = 8000  # Port to listen for IBC packets

        # Set up logging
        self.logs_dir = '/home/ubuntu/IBC_Simulation/mininet_shared/logs'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        self.log_file = os.path.join(self.logs_dir, f'{self.node_name}_transfer_log.txt')
        self.log('Relayer initialized.')

    def log(self, message):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} {message}\n")
        print(f"{timestamp} {message}")

    def start(self):
        threading.Thread(target=self.listen_zone, daemon=True).start()
        threading.Thread(target=self.listen_hub, daemon=True).start()
        while True:
            time.sleep(10)

    def listen_zone(self):
        # Listen for IBC packets from Zone
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.zone_ip, self.listen_port))
            s.listen()
            self.log(f"Listening for IBC packets from Zone on {self.zone_ip}:{self.listen_port}")
            while True:
                conn, addr = s.accept()
                data = conn.recv(1024)
                if data:
                    message = data.decode()
                    self.log(f"Received packet from Zone: {message}")
                    self.forward_to_hub(message)

    def listen_hub(self):
        # Listen for IBC packets from Hub
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.hub_ip, self.listen_port))
            s.listen()
            self.log(f"Listening for IBC packets from Hub on {self.hub_ip}:{self.listen_port}")
            while True:
                conn, addr = s.accept()
                data = conn.recv(1024)
                if data:
                    message = data.decode()
                    self.log(f"Received packet from Hub: {message}")
                    self.forward_to_zone(message)

    def forward_to_hub(self, message):
        # Forward packet to Hub
        dest_ip = '10.0.0.1'  # Hub node IP (adjust as needed)
        port = 8000
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((dest_ip, port))
                s.sendall(message.encode())
                self.log(f"Forwarded packet to Hub at {dest_ip}:{port}")
        except Exception as e:
            self.log(f"Error forwarding packet to Hub: {e}")

    def forward_to_zone(self, message):
        # Forward packet to Zone
        dest_ip = self.zone_ip.replace('.10', '.1')  # Assuming zone node IP ends with .1
        port = 8000
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((dest_ip, port))
                s.sendall(message.encode())
                self.log(f"Forwarded packet to Zone at {dest_ip}:{port}")
        except Exception as e:
            self.log(f"Error forwarding packet to Zone: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 relayer.py <node_name> <zone_label>")
        sys.exit(1)
    relayer = Relayer(sys.argv[1], sys.argv[2])
    relayer.start()