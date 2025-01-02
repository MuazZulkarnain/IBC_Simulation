#!/usr/bin/env python3

import sys
import threading
import socket
import time
import os

class ZoneNode:
    def __init__(self, node_name):
        self.node_name = node_name
        self.zone_id = self.node_name.split('_')[0]  # Extract 'z1' from 'z1_v1'
        self.zone_index = int(self.zone_id[1:])  # Extract index 1 from 'z1'
        self.balance = 100000  # Initial token balance
        self.ibc_clients = {}  # Clients for other chains
        self.connections = {}  # Connections to other chains
        self.channels = {}     # Channels for applications
        self.listen_port = 8000

        # Set up logging
        self.logs_dir = '/home/ubuntu/IBC_Simulation/mininet_shared/logs'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        self.log_file = os.path.join(self.logs_dir, f'{self.node_name}_transfer_log.txt')
        self.transaction_results_file = os.path.join(self.logs_dir, f'{self.node_name}_transaction_results.csv')
        self.init_transaction_results_file()
        self.log('Node initialized.')

    def init_transaction_results_file(self):
        # Initialize transaction_results.csv file with headers
        if not os.path.exists(self.transaction_results_file):
            with open(self.transaction_results_file, 'w') as f:
                f.write('transaction_id,timestamp,source_zone,destination_zone,amount\n')

    def log(self, message):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} {message}\n")
        print(f"{timestamp} {message}")

    def start(self):
        threading.Thread(target=self.ibc_listener, daemon=True).start()
        threading.Thread(target=self.command_listener, daemon=True).start()
        self.run_node()

    def run_node(self):
        while True:
            self.log(f"Running Zone node. Balance: {self.balance}")
            time.sleep(10)

    def ibc_listener(self):
        # Listen for IBC messages
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
                conn.close()

    def handle_ibc_message(self, message):
        # Simplified message handling
        if message.startswith('IBC_TRANSFER'):
            # Message format: 'IBC_TRANSFER,<amount>,<sender_zone>,<sender>,<destination_zone>,<transaction_id>'
            parts = message.strip().split(',')
            if len(parts) == 6:
                _, amount_str, sender_zone, sender, dest_zone, transaction_id = parts
                amount = int(amount_str)
                self.balance += amount
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.log(f"Received {amount} tokens from {sender} (Zone {sender_zone}). New balance: {self.balance}")

                # Log transaction completion
                with open(self.transaction_results_file, 'a') as f:
                    f.write(f"{transaction_id},{timestamp},{sender_zone},{dest_zone},{amount}\n")
            else:
                self.log(f"Malformed IBC_TRANSFER message: {message}")
        else:
            self.log(f"Unknown IBC message type: {message}")

    def initiate_transfer(self, dest_zone, amount, transaction_id):
        # Reduce balance
        if self.balance >= amount:
            self.balance -= amount
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"Initiating transfer {transaction_id} of {amount} tokens to Zone {dest_zone}. New balance: {self.balance}")

            # Send IBC packet to relayer
            relayer_ip = f'10.0.{self.zone_index}.10'  # Adjust as per your IP scheme
            relayer_port = 8000
            packet = f'IBC_TRANSFER,{amount},{self.zone_id},{self.node_name},{dest_zone},{transaction_id}'
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    self.log(f"Connecting to relayer at {relayer_ip}:{relayer_port}")
                    s.connect((relayer_ip, relayer_port))
                    s.sendall(packet.encode())
                    self.log(f"Sent IBC packet {transaction_id} to relayer at {relayer_ip}:{relayer_port}")
            except Exception as e:
                self.log(f"Error sending IBC packet to relayer: {e}")
        else:
            self.log(f"Insufficient balance to transfer {amount} tokens")

    def command_listener(self):
        # Listen for commands on a separate port
        cmd_port = 8001
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', cmd_port))
            s.listen()
            self.log(f"Listening for transfer commands on port {cmd_port}")
            while True:
                conn, addr = s.accept()
                data = conn.recv(1024)
                if data:
                    message = data.decode()
                    self.log(f"Received command: {message}")
                    cmd_parts = message.strip().split()
                    if cmd_parts[0] == 'transfer' and len(cmd_parts) == 4:
                        destination_zone = cmd_parts[1]
                        amount = int(cmd_parts[2])
                        transaction_id = cmd_parts[3]
                        self.initiate_transfer(destination_zone, amount, transaction_id)
                    elif cmd_parts[0] == 'balance':
                        self.log(f"Current balance: {self.balance}")
                    else:
                        self.log(f"Unknown command: {message}")
                conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 zone_node.py <node_name>")
        sys.exit(1)
    node = ZoneNode(sys.argv[1])
    node.start()