#!/usr/bin/env python3

import sys
import time
import threading
import random
import socket

class SimulationController:
    def __init__(self, duration=60):
        self.duration = duration  # Simulation duration in seconds
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

    def start(self):
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        print("Simulation is running...")
        self.run_simulation()
        self.print_summary()

    def run_simulation(self):
        while time.time() < self.end_time:
            # Very short delay between transactions
            delay = 0.00001  # in seconds
            time.sleep(delay)

            # Randomly select source and destination zones
            source_zone = random.choice(self.zones)
            destination_zone = random.choice([z for z in self.zones if z != source_zone])

            # Random amount between 1 and 10 tokens
            amount = random.randint(1, 10)

            # Increment transaction ID
            self.transaction_id += 1

            # Send transfer command
            self.send_transfer_command(source_zone, destination_zone, amount, self.transaction_id)

        print("Simulation completed.")

    def send_transfer_command(self, source_zone, destination_zone, amount, transaction_id):
        node_ip = self.nodes[source_zone]
        command = f"transfer {destination_zone} {amount} {transaction_id}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Log the transaction initiation
        with open(self.log_file, 'a') as f:
            f.write(f"{transaction_id},{timestamp},{source_zone},{destination_zone},{amount}\n")

        # Determine the source IP to use
        source_ip = self.source_ips.get(source_zone)
        if source_ip is None:
            print(f"Error: No source IP available for Zone {source_zone}")
            return

        # Send the command to the source node
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((source_ip, 0))
                s.connect((node_ip, self.cmd_port))
                s.sendall(command.encode())
                # Optionally, remove or comment out the print statement to reduce console output
                # print(f"Sent transaction {transaction_id} from Zone {source_zone} to Zone {destination_zone}: {amount} tokens")
        except Exception as e:
            print(f"Error sending command to {node_ip}: {e}")

    def print_summary(self):
        total_transactions = self.transaction_id
        print(f"Total transactions completed: {total_transactions}")

if __name__ == '__main__':
    controller = SimulationController(duration=60)
    controller.start()