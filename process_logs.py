#!/usr/bin/env python3

import csv
from datetime import datetime
import matplotlib.pyplot as plt

def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def main():
    # Paths to the log files
    sim_log_file = '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/simulation_transactions.csv'
    result_files = [
        '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/za_v1_transaction_results.csv',
        '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/zb_v1_transaction_results.csv',
        '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/zc_v1_transaction_results.csv',
    ]

    # Read simulation transactions
    transactions = {}
    with open(sim_log_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions[row['transaction_id']] = {
                'init_time': parse_timestamp(row['timestamp']),
                'source_zone': row['source_zone'],
                'destination_zone': row['destination_zone'],
                'amount': int(row['amount']),
            }

    # Read transaction results
    for result_file in result_files:
        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transaction_id = row['transaction_id']
                if transaction_id in transactions:
                    transactions[transaction_id]['completion_time'] = parse_timestamp(row['timestamp'])

    # Calculate latency and other metrics
    latencies = []
    transaction_times = []
    for tx in transactions.values():
        if 'completion_time' in tx:
            latency = (tx['completion_time'] - tx['init_time']).total_seconds()
            latencies.append(latency)
            transaction_times.append(tx['init_time'])

    # Plot transactions over time
    plt.figure(figsize=(10, 5))
    plt.hist([tx['init_time'] for tx in transactions.values()], bins=60, edgecolor='black')
    plt.xlabel('Time')
    plt.ylabel('Number of Transactions')
    plt.title('Transactions Over Time')
    plt.show()

    # Plot latency distribution
    plt.figure(figsize=(10, 5))
    plt.hist(latencies, bins=20, edgecolor='black')
    plt.xlabel('Latency (seconds)')
    plt.ylabel('Number of Transactions')
    plt.title('Transaction Latency Distribution')
    plt.show()

if __name__ == '__main__':
    main()