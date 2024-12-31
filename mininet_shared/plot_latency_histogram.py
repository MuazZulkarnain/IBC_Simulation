#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-GUI environments
import csv
import matplotlib.pyplot as plt

def main():
    latency_csv_file = '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/latency_results.csv'

    latencies = []

    try:
        with open(latency_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                latency = float(row['latency'])
                latencies.append(latency)

        if not latencies:
            print("No latency data found in 'latency_results.csv'.")
            return

        # Plot Latency Distribution
        plt.figure(figsize=(10, 5))
        plt.hist(latencies, bins=50, edgecolor='black')
        plt.xlabel('Latency (seconds)')
        plt.ylabel('Number of Transactions')
        plt.title('Transaction Latency Distribution')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/latency_distribution_histogram.png')
        print("Plot saved as 'latency_distribution.png' in the logs directory.")
    except FileNotFoundError:
        print(f"File '{latency_csv_file}' not found. Please ensure the file exists and contains data.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()