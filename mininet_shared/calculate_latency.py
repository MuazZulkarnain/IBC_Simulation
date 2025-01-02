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
            transactions[transaction_id] = {
                'init_time': parse_timestamp(row['timestamp']),
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
                        transactions[transaction_id]['completion_time'] = parse_timestamp(row['timestamp'])
                    else:
                        print(f"Warning: Transaction ID {transaction_id} found in {result_file} but not in simulation log.")
        except FileNotFoundError:
            print(f"File {result_file} not found. Skipping.")
    
    # Calculate latency
    latency_data = []
    for tx_id, tx in transactions.items():
        if tx['completion_time']:
            latency = (tx['completion_time'] - tx['init_time']).total_seconds()
            latency_data.append({
                'transaction_id': tx_id,
                'latency': latency,
                'source_zone': tx['source_zone'],
                'destination_zone': tx['destination_zone'],
                'amount': tx['amount'],
            })
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

if __name__ == '__main__':
    main()