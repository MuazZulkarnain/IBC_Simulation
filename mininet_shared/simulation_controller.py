#!/usr/bin/env python3

import sys
import time
import random
import asyncio
import socket
import json
import os

class SimulationController:
    def __init__(self, duration=60, tps=1000, config_file='zone_configs.json'):
        self.duration = duration  # Simulation duration in seconds
        self.tps = tps  # Desired transactions per second
        self.start_time = None
        self.end_time = None
        self.transaction_id = 0  # Counter for transaction IDs

        # Load zones and nodes from configuration file
        self.zones = []
        self.nodes = {}       # Mapping from zone ID to node IP address
        self.source_ips = {}  # Mapping from zone ID to source IP address

        self.cmd_port = 8001

        # Metrics storage
        self.transactions_sent = 0
        self.transactions_completed = 0
        self.transactions_failed = 0
        self.latencies = []
        self.transactions_per_second = {}
        self.throughput_per_second = {}
        self.lock = asyncio.Lock()

        # Errors encountered
        self.errors = []

        # Load configuration
        self.load_configuration(config_file)

    def load_configuration(self, config_file):
        # Define the path to the shared directory
        shared_dir = '/home/ubuntu/IBC_Simulation/mininet_shared'

        config_path = os.path.join(shared_dir, config_file)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

        # Read the JSON configuration file
        with open(config_path, 'r') as f:
            zone_configs = json.load(f)

        # Initialize zones, nodes, and source IPs
        for zone_config in zone_configs:
            zone_id = zone_config['id']
            zone_name = zone_config['name']
            validator_ip = zone_config['validator_ip']
            controller_ip = zone_config['controller_ip']

            self.zones.append(zone_id)  # Use zone IDs as identifiers

            # Map zone IDs to validator IPs (nodes)
            self.nodes[zone_id] = validator_ip

            # Map zone IDs to controller IPs (source IPs)
            self.source_ips[zone_id] = controller_ip

        print(f"Loaded configuration for zones: {self.zones}")

    async def start(self):
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        print(f"Simulation is running for {self.duration} seconds at {self.tps} TPS...")

        await self.run_simulation()
        await asyncio.sleep(0)  # Allow any pending tasks to complete

        self.print_summary()
        self.log_detailed_data()
        self.log_errors()

    async def run_simulation(self):
        delay = 1 / self.tps  # Delay between transactions based on TPS
        next_transaction_time = time.time()

        tasks = []

        while time.time() < self.end_time:
            now = time.time()
            if now >= next_transaction_time:
                # Schedule the transaction
                task = asyncio.create_task(self.create_and_send_transaction())
                tasks.append(task)

                # Schedule next transaction
                next_transaction_time += delay

                # If we're behind schedule, adjust without sleeping
                if next_transaction_time < now:
                    next_transaction_time = now
            else:
                # Sleep until the next scheduled transaction time
                time_to_sleep = next_transaction_time - now
                if time_to_sleep > 0:
                    await asyncio.sleep(time_to_sleep)

        print("All transactions have been scheduled. Waiting for completion...")

        # Wait for all scheduled transactions to complete
        await asyncio.gather(*tasks)
        print("Simulation completed.")

    async def create_and_send_transaction(self):
        # Randomly select source and destination zones
        source_zone = random.choice(self.zones)
        destination_zone = random.choice([z for z in self.zones if z != source_zone])

        # Random amount between 1 and 10 tokens
        amount = random.randint(1, 10)

        # Increment transaction ID
        async with self.lock:
            self.transaction_id += 1
            transaction_id = self.transaction_id

        # Send transfer command
        await self.send_transfer_command(source_zone, destination_zone, amount, transaction_id)

    async def send_transfer_command(self, source_zone, destination_zone, amount, transaction_id):
        command = f"transfer {destination_zone} {amount} {transaction_id}"

        node_ip = self.nodes.get(source_zone)
        source_ip = self.source_ips.get(source_zone)

        if node_ip is None or source_ip is None:
            error_msg = f"Error: Missing node or source IP for Zone {source_zone}"
            async with self.lock:
                self.errors.append(error_msg)
                self.transactions_failed += 1
            return

        send_time = time.time()  # Time when the transaction is sent

        # Update transactions sent per second
        async with self.lock:
            self.transactions_sent += 1
            second = int(send_time - self.start_time)
            self.transactions_per_second[second] = self.transactions_per_second.get(second, 0) + 1

        # Send the command to the source node using a per-transaction connection
        try:
            reader, writer = await asyncio.open_connection(
                host=node_ip,
                port=self.cmd_port,
                local_addr=(source_ip, 0)
            )
            writer.write(command.encode())
            await writer.drain()

            # Not waiting for server response
            writer.close()
            await writer.wait_closed()

            receive_time = time.time()  # Time after the data has been sent
            send_duration = receive_time - send_time  # Time taken to send the data

            # Update metrics
            async with self.lock:
                self.transactions_completed += 1
                # If desired, record send_duration
                # self.latencies.append(send_duration)
                second = int(receive_time - self.start_time)
                self.throughput_per_second[second] = self.throughput_per_second.get(second, 0) + 1

        except Exception as e:
            error_msg = f"Error sending command to {source_zone} (Transaction ID {transaction_id}): {e}"
            async with self.lock:
                self.errors.append(error_msg)
                self.transactions_failed += 1

    def print_summary(self):
        total_transactions = self.transactions_sent
        completed_transactions = self.transactions_completed
        failed_transactions = self.transactions_failed

        print("\n--- Simulation Summary ---")
        print(f"Total transactions sent: {total_transactions}")
        print(f"Total transactions completed: {completed_transactions}")
        print(f"Total transactions failed: {failed_transactions}")

        # Optionally print average send duration if recorded
        average_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        print(f"Average send duration: {average_latency * 1000:.2f} ms")

    def log_detailed_data(self):
        # Log detailed metrics to a file
        summary_lines = []

        summary_lines.append("Send Rate Per Second:")
        for second in sorted(self.transactions_per_second.keys()):
            summary_lines.append(f"Second {second}: {self.transactions_per_second[second]} transactions")

        summary_lines.append("\nThroughput Per Second:")
        for second in sorted(self.throughput_per_second.keys()):
            summary_lines.append(f"Second {second}: {self.throughput_per_second[second]} transactions")

        # Join all lines into a single string
        summary = "\n".join(summary_lines)

        # Write summary to a file
        with open('simulation_detailed_log.txt', 'w') as f:
            f.write(summary)

    def log_errors(self):
        if self.errors:
            # Write errors to a separate log file
            with open('simulation_errors.log', 'w') as f:
                for error in self.errors:
                    f.write(error + '\n')

            # Optionally print errors to console
            print("\nErrors encountered during simulation:")
            for error in self.errors:
                print(error)

if __name__ == '__main__':
    controller = SimulationController(duration=5, tps=1000, config_file='zone_configs.json')

    # Run the simulation using asyncio event loop
    asyncio.run(controller.start())