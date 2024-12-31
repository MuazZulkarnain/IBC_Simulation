#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-GUI environments
import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter

def main():
    latency_csv_file = '/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/latency_results.csv'

    try:
        transaction_ids = []
        latencies = []

        with open(latency_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use transaction initiation times or transaction IDs for x-axis
                transaction_id = int(row['transaction_id'])
                latency = float(row['latency'])
                transaction_ids.append(transaction_id)
                latencies.append(latency)

        if not latencies:
            print("No latency data found in 'latency_results.csv'.")
            return

        # Sort data by transaction ID
        sorted_pairs = sorted(zip(transaction_ids, latencies))
        x_vals, y_vals = zip(*sorted_pairs)

        # Convert to numpy arrays
        x_vals = np.array(x_vals)
        y_vals = np.array(y_vals)

        # Apply Savitzky-Golay filter for smoothing
        window_size = 101  # Choose an odd window size greater than the polynomial order
        poly_order = 3     # Polynomial order for fitting

        # Ensure that window_size does not exceed the length of data
        if len(y_vals) < window_size:
            window_size = len(y_vals) // 2 * 2 + 1  # Make it the largest odd number less than len(y_vals)

        y_smooth = savgol_filter(y_vals, window_size, poly_order)

        # Plotting
        plt.figure(figsize=(12, 6))
        plt.plot(x_vals, y_smooth, color='blue', label='Smoothed Latency Curve')
        plt.scatter(x_vals, y_vals, color='red', s=10, label='Actual Latency Data')
        plt.xlabel('Transaction ID')
        plt.ylabel('Latency (seconds)')
        plt.title('Transaction Latency Over Time')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('/home/ubuntu/mn_blockchain/cosmos_complex/mininet_shared/logs/latency_line_plot.png')
        print("Plot saved as 'latency_line_plot.png' in the logs directory.")

    except FileNotFoundError:
        print(f"File '{latency_csv_file}' not found. Please ensure the file exists and contains data.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()