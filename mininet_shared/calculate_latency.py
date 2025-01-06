#!/usr/bin/env python3

import csv
from datetime import datetime
import os
import sys
import json
import statistics

def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def main():
    # Paths to the shared directory
    shared_dir = '/home/ubuntu/IBC_Simulation/mininet_shared'
    
    # Ensure the logs directory exists
    os.makedirs(os.path.join(shared_dir, 'logs'), exist_ok=True)
    
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
    
    # Initialize variables for summary statistics
    simulation_start_time = None
    simulation_end_time = None

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
        if simulation_start_time is None or init_time < simulation_start_time:
            simulation_start_time = init_time
        init_seconds = int(init_time.timestamp())
        send_rate_per_second[init_seconds] = send_rate_per_second.get(init_seconds, 0) + 1

        if tx['completion_time']:
            completion_time = tx['completion_time']
            if simulation_end_time is None or completion_time > simulation_end_time:
                simulation_end_time = completion_time
            latency = (completion_time - init_time).total_seconds()
            latency_data.append({
                'transaction_id': tx_id,
                'latency': latency,
                'source_zone': tx['source_zone'],
                'destination_zone': tx['destination_zone'],
                'amount': tx['amount'],
                'init_time': init_time,
                'completion_time': completion_time,
            })
            completion_seconds = int(completion_time.timestamp())
            throughput_per_second[completion_seconds] = throughput_per_second.get(completion_seconds, 0) + 1
        else:
            # If transaction hasn't completed, consider its initiation time as potential end time
            if simulation_end_time is None or init_time > simulation_end_time:
                simulation_end_time = init_time

    # Ensure simulation_end_time is set
    if simulation_end_time is None:
        simulation_end_time = max(tx['init_time'] for tx in transactions.values())

    # Write latency data to CSV
    latency_csv_file = os.path.join(shared_dir, 'logs', 'latency_results.csv')
    with open(latency_csv_file, 'w', newline='') as f:
        fieldnames = ['transaction_id', 'latency', 'source_zone', 'destination_zone', 'amount', 'init_time', 'completion_time']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in latency_data:
            # Convert datetime objects to strings for CSV output
            data['init_time'] = data['init_time'].strftime('%Y-%m-%d %H:%M:%S')
            data['completion_time'] = data['completion_time'].strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(data)
    
    # Collect latencies for summary statistics
    latencies = [data['latency'] for data in latency_data]

    # Summary Statistics Computations

    # 1. Time taken for simulation
    simulation_duration = (simulation_end_time - simulation_start_time).total_seconds()

    # 2. Total transactions processed
    total_transactions_processed = len([tx for tx in transactions.values() if tx['completion_time']])

    # 3. Average throughput per second
    if throughput_per_second:
        total_throughput_transactions = sum(throughput_per_second.values())
        throughput_seconds = sorted(throughput_per_second.keys())
        throughput_duration = throughput_seconds[-1] - throughput_seconds[0] + 1
        average_throughput = total_throughput_transactions / throughput_duration
    else:
        average_throughput = 0

    # 4. Standard deviation of throughput
    if throughput_per_second and len(throughput_per_second) > 1:
        throughput_values = list(throughput_per_second.values())
        std_dev_throughput = statistics.stdev(throughput_values)
    else:
        std_dev_throughput = 0.0

    # 5. Time taken to finish sending transactions
    send_times = [tx['init_time'] for tx in transactions.values()]
    send_start_time = min(send_times)
    send_end_time = max(send_times)
    send_duration = (send_end_time - send_start_time).total_seconds()

    # 6. Average send rate per second
    if send_rate_per_second:
        total_send_transactions = sum(send_rate_per_second.values())
        send_seconds = sorted(send_rate_per_second.keys())
        send_duration_seconds = send_seconds[-1] - send_seconds[0] + 1
        average_send_rate = total_send_transactions / send_duration_seconds
    else:
        average_send_rate = 0

    # 7. Standard deviation of send rate
    if send_rate_per_second and len(send_rate_per_second) > 1:
        send_rate_values = list(send_rate_per_second.values())
        std_dev_send_rate = statistics.stdev(send_rate_values)
    else:
        std_dev_send_rate = 0.0

    # 8. Time taken to finish processing all transactions
    processing_duration = (simulation_end_time - simulation_start_time).total_seconds()

    # 9. Total number of transactions failed/dropped
    total_transactions_attempted = len(transactions)
    transactions_failed = total_transactions_attempted - total_transactions_processed

    # 10. Error rate for the entire run
    if total_transactions_attempted:
        error_rate = (transactions_failed / total_transactions_attempted) * 100
    else:
        error_rate = 0
    
    # 11. Average latency
    if latencies:
        average_latency = sum(latencies) / len(latencies)
    else:
        average_latency = 0.0

    # 12. Maximum latency
    if latencies:
        max_latency = max(latencies)
    else:
        max_latency = 0.0

    # Print summary statistics
    print("\nSummary Statistics:")
    print("-------------------")
    print(f"Time Taken for Simulation: {simulation_duration:.2f} seconds")
    print(f"Time Taken to Finish Sending Transactions: {send_duration:.2f} seconds")
    print(f"Time Taken to Finish Processing All Transactions: {processing_duration:.2f} seconds")
    print(f"Total Transactions Processed: {total_transactions_processed}")
    print(f"Average Throughput per Second: {average_throughput:.4f} transactions/second")
    print(f"Standard Deviation of Throughput: {std_dev_throughput:.4f}")
    print(f"Average Send Rate per Second: {average_send_rate:.4f} transactions/second")
    print(f"Standard Deviation of Send Rate: {std_dev_send_rate:.4f}")
    print(f"Total Number of Transactions Failed/Dropped: {transactions_failed}")
    print(f"Error Rate for Entire Run: {error_rate:.2f}%")
    print(f"Average Latency: {average_latency:.4f} seconds")
    print(f"Maximum Latency: {max_latency:.4f} seconds")

    # Generate a run identifier (e.g., timestamp)
    run_id = datetime.now().strftime('%Y%m%d%H%M%S')

    # Optionally, write send rate and throughput per second to a CSV file
    rates_csv_file = os.path.join(shared_dir, 'logs', 'rates_per_second.csv')
    # Check if the CSV file exists and if it's empty
    file_exists = os.path.isfile(rates_csv_file)
    file_is_empty = not os.path.exists(rates_csv_file) or os.path.getsize(rates_csv_file) == 0

    # Open the CSV file in append mode
    with open(rates_csv_file, 'a', newline='') as f:
        fieldnames = ['run_id', 'second', 'time', 'send_rate', 'throughput']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write the header only if the file doesn't exist or is empty
        if not file_exists or file_is_empty:
            writer.writeheader()
        # Get the union of all seconds
        all_seconds = set(send_rate_per_second.keys()).union(throughput_per_second.keys())
        for second in sorted(all_seconds):
            time_str = datetime.fromtimestamp(second).strftime('%Y-%m-%d %H:%M:%S')
            send_rate = send_rate_per_second.get(second, 0)
            throughput = throughput_per_second.get(second, 0)
            writer.writerow({
                'run_id': run_id,
                'second': second,
                'time': time_str,
                'send_rate': send_rate,
                'throughput': throughput
            })

    # Write summary statistics to CSV
    summary_csv_file = os.path.join(shared_dir, 'summary_statistics.csv')  # Changed path to output in main directory
    # Check if the CSV file exists and is not empty
    file_exists = os.path.isfile(summary_csv_file)
    file_is_empty = not os.path.exists(summary_csv_file) or os.path.getsize(summary_csv_file) == 0

    # Prepare the data to be written
    summary_data = {
        'run_id': run_id,
        'Time Taken for Simulation (seconds)': f"{simulation_duration:.2f}",
        'Time Taken to Finish Sending Transactions (seconds)': f"{send_duration:.2f}",
        'Time Taken to Finish Processing All Transactions (seconds)': f"{processing_duration:.2f}",
        'Total Transactions Processed': total_transactions_processed,
        'Average Throughput per Second (transactions/second)': f"{average_throughput:.4f}",
        'Standard Deviation of Throughput': f"{std_dev_throughput:.4f}",
        'Average Send Rate per Second (transactions/second)': f"{average_send_rate:.4f}",
        'Standard Deviation of Send Rate': f"{std_dev_send_rate:.4f}",
        'Total Number of Transactions Failed/Dropped': transactions_failed,
        'Error Rate for Entire Run (%)': f"{error_rate:.2f}",
        'Average Latency (seconds)': f"{average_latency:.4f}",
        'Maximum Latency (seconds)': f"{max_latency:.4f}",
    }

    # List of field names (keys) for the CSV header
    fieldnames = list(summary_data.keys())

    # Open the CSV file in append mode
    with open(summary_csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write the header only if the file doesn't exist or is empty
        if not file_exists or file_is_empty:
            writer.writeheader()
        # Write the summary data
        writer.writerow(summary_data)

    print(f"\nSummary statistics have been appended to {summary_csv_file}")
    print(f"Rates per second have been appended to {rates_csv_file}")

if __name__ == '__main__':
    main()