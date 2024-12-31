#!/usr/bin/env python3

import sys
import time
import random
import socket
from concurrent.futures import ThreadPoolExecutor
import threading

class SimulationController:
    def __init__(self, duration=60, tps=1000):
        self.duration = duration  # Simulation duration in seconds
        self.tps = tps  # Desired transactions per second
        self.start_time = None
        self.transaction_id = 0  # Counter for transaction IDs
        self.zones = ['A', 'B', 'C']  # Available zones

        # Node IP addresses
        self.nodes = {
            'A': '10.0.1.1',
            'B': '10.0.2.1',
            'C': '10.0.3.1',
        }

        self.cmd_port = 8001

        # Log file
        self.log_file = '/home/ubuntu/IBC_Simulation/mininet_shared/logs/simulation_transactions.csv'

        # Initialize log file with headers
        with open(self.log_file, 'w') as f:
            f.write('transaction_id,timestamp,source_zone,destination_zone,amount\n')

        # Source IPs
        self.source_ips = {
            'A': '10.0.1.200',
            'B': '10.0.2.200',
            'C': '10.0.3.200',
        }

        # Thread pool for handling transactions
        self.executor = ThreadPoolExecutor(max_workers=200)  # Adjust max_workers as needed

        # For batch logging
        self.log_entries = []
        self.log_lock = threading.Lock()

    def start(self):
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        print(f"Simulation is running for {self.duration} seconds at {self.tps} TPS...")
        self.run_simulation()
        self.executor.shutdown(wait=True)
        self.print_summary()
        # Flush remaining log entries
        if self.log_entries:
            with self.log_lock:
                with open(self.log_file, 'a') as f:
                    f.writelines(self.log_entries)
                self.log_entries = []

    def run_simulation(self):
        delay = 1 / self.tps  # Delay between transactions based on TPS
        next_transaction_time = time.time()

        while time.time() < self.end_time:
            now = time.time()
            if now >= next_transaction_time:
                # Randomly select source and destination zones
                source_zone = random.choice(self.zones)
                destination_zone = random.choice([z for z in self.zones if z != source_zone])

                # Random amount between 1 and 10 tokens
                amount = random.randint(1, 10)

                # Increment transaction ID
                self.transaction_id += 1
                transaction_id = self.transaction_id

                # Submit transaction to the executor
                self.executor.submit(self.process_transaction, source_zone, destination_zone, amount, transaction_id)

                # Schedule next transaction
                next_transaction_time += delay

                # If we're behind schedule, adjust without sleeping
                if next_transaction_time < now:
                    next_transaction_time = now
            else:
                # Sleep until the next scheduled transaction time
                time_to_sleep = next_transaction_time - now
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

        print("Simulation completed.")

    def process_transaction(self, source_zone, destination_zone, amount, transaction_id):
        self.send_transfer_command(source_zone, destination_zone, amount, transaction_id)

    def send_transfer_command(self, source_zone, destination_zone, amount, transaction_id):
        command = f"transfer {destination_zone} {amount} {transaction_id}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Log the transaction initiation
        log_entry = f"{transaction_id},{timestamp},{source_zone},{destination_zone},{amount}\n"

        # Collect log entries in a list for batch logging
        with self.log_lock:
            self.log_entries.append(log_entry)
            # Batch write to log file if enough entries are collected
            if len(self.log_entries) >= 1000:
                with open(self.log_file, 'a') as f:
                    f.writelines(self.log_entries)
                self.log_entries = []

        node_ip = self.nodes[source_zone]
        source_ip = self.source_ips.get(source_zone)
        if source_ip is None:
            print(f"Error: No source IP available for Zone {source_zone}")
            return

        # Send the command to the source node using a per-transaction socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((source_ip, 0))
                s.connect((node_ip, self.cmd_port))
                s.sendall(command.encode())
                s.shutdown(socket.SHUT_WR)
                # Optional: read the server's response if necessary
                # response = s.recv(1024)
        except Exception as e:
            print(f"Error sending command to {source_zone}: {e}")

    def print_summary(self):
        total_transactions = self.transaction_id
        print(f"Total transactions completed: {total_transactions}")

if __name__ == '__main__':
    # Adjust the TPS and max_workers as needed
    controller = SimulationController(duration=10, tps=1000)
    controller.start()