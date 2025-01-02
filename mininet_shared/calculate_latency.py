#!/usr/bin/env python3

import csv
from datetime import datetime
import os
import sys
import json

def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def main():
    # Paths to the shared directory
    shared_dir = '/home/ubuntu/IBC_Simulation/mininet_shared'
    
    # Path to the simulation transactions log file
    sim_log_file = os.path.join(shared_dir, 'logs', 'simulation_transactions.csv')
    
    # Read zone configurations from shared JSON file
    config_file = os.path.join(shared_dir, 'zone_configs.json')

    if not os.path.exists(config_file):
        print(f"Configuration file '{config_file}' not found.")
        sys.exit(1)

    # Load the zone configurations
    with open(config_file, 'r') as f:
        zone_configs = json.load(f)

    # Collect zone IDs and validator node names
    zone_ids = []
    validator_node_names = []

    for zone_config in zone_configs:
        zone_id = zone_config['id']  # e.g., 'z1'
        zone_ids.append(zone_id)
        # Node names should be 'z1_v1', 'z2_v1', etc.
        validator_node_names.append(f'{zone_id}_v1')

    # Generate the result_files list based on the validator node names
    result_files = [
        os.path.join(shared_dir, 'logs', f'{node_name}_transaction_results.csv')
        for node_name in validator_node_names
    ]
    
    # Read simulation transactions (initiation times)
    transactions = {}
    if not os.path.exists(sim_log_file):
        print(f"Simulation transactions file '{sim_log_file}' not found.")
        sys.exit(1)
    
    with open(sim_log_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transaction_id = row['transaction_id']
            init_time = parse_timestamp(row['timestamp'])
            transactions[transaction_id] = {
                'init_time': init_time,
                'source_zone': row['source_zone'],
                'destination_zone': row['destination_zone'],
                'amount': int(row['amount']),
                'completion_time': None,  # Placeholder for completion time
            }
    
    # Read transaction results (completion times)
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transaction_id = row['transaction_id']
                    if transaction_id in transactions:
                        completion_time = parse_timestamp(row['timestamp'])
                        transactions[transaction_id]['completion_time'] = completion_time
                    else:
                        print(f"Warning: Transaction ID {transaction_id} found in {result_file} but not in simulation log.")
        except FileNotFoundError:
            print(f"File {result_file} not found. Skipping.")
    
    # Calculate latency and collect rates per second
    latency_data = []
    send_rate_per_second = {}
    throughput_per_second = {}

    for tx_id, tx in transactions.items():
        init_time = tx['init_time']
        init_seconds = int(init_time.timestamp())
        # Update send rate per second
        send_rate_per_second[init_seconds] = send_rate_per_second.get(init_seconds, 0) + 1

        if tx['completion_time']:
            completion_time = tx['completion_time']
            latency = (completion_time - init_time).total_seconds()
            latency_data.append({
                'transaction_id': tx_id,
                'latency': latency,
                'source_zone': tx['source_zone'],
                'destination_zone': tx['destination_zone'],
                'amount': tx['amount'],
            })
            completion_seconds = int(completion_time.timestamp())
            # Update throughput per second
            throughput_per_second[completion_seconds] = throughput_per_second.get(completion_seconds, 0) + 1
        else:
            print(f"Warning: Transaction ID {tx_id} has no completion time. It may still be in progress or an error occurred.")

    # Write latency data to CSV
    latency_csv_file = os.path.join(shared_dir, 'logs', 'latency_results.csv')
    with open(latency_csv_file, 'w', newline='') as f:
        fieldnames = ['transaction_id', 'latency', 'source_zone', 'destination_zone', 'amount']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in latency_data:
            writer.writerow(data)
    
    # Print summary statistics
    latencies = [data['latency'] for data in latency_data]
    if latencies:
        average_latency = sum(latencies) / len(latencies)
        print(f"Average Transaction Latency: {average_latency:.4f} seconds")
        print(f"Total Transactions Processed: {len(latencies)}")
    else:
        print("No transactions processed.")

    # Print Send Rate Per Second
    print("\nSend Rate Per Second:")
    for second in sorted(send_rate_per_second.keys()):
        count = send_rate_per_second[second]
        time_str = datetime.fromtimestamp(second).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{time_str}: {count} transactions")

    # Print Throughput Per Second
    print("\nThroughput Per Second:")
    for second in sorted(throughput_per_second.keys()):
        count = throughput_per_second[second]
        time_str = datetime.fromtimestamp(second).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{time_str}: {count} transactions")

    # Optionally, write send rate and throughput per second to a CSV file
    rates_csv_file = os.path.join(shared_dir, 'logs', 'rates_per_second.csv')
    with open(rates_csv_file, 'w', newline='') as f:
        fieldnames = ['second', 'time', 'send_rate', 'throughput']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Get the union of all seconds
        all_seconds = set(send_rate_per_second.keys()).union(throughput_per_second.keys())
        for second in sorted(all_seconds):
            time_str = datetime.fromtimestamp(second).strftime('%Y-%m-%d %H:%M:%S')
            send_rate = send_rate_per_second.get(second, 0)
            throughput = throughput_per_second.get(second, 0)
            writer.writerow({
                'second': second,
                'time': time_str,
                'send_rate': send_rate,
                'throughput': throughput
            })

if __name__ == '__main__':
    main()