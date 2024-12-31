#!/usr/bin/env python3

import csv
from datetime import datetime

def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def main():
    # Paths to the log files
    sim_log_file = '/home/ubuntu/IBC_Simulation/mininet_shared/logs/simulation_transactions.csv'
    result_files = [
        '/home/ubuntu/IBC_Simulation/mininet_shared/logs/za_v1_transaction_results.csv',
        '/home/ubuntu/IBC_Simulation/mininet_shared/logs/zb_v1_transaction_results.csv',
        '/home/ubuntu/IBC_Simulation/mininet_shared/logs/zc_v1_transaction_results.csv',
    ]

    # Read simulation transactions (initiation times)
    transactions = {}
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
    latency_csv_file = '/home/ubuntu/IBC_Simulation/mininet_shared/logs/latency_results.csv'
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