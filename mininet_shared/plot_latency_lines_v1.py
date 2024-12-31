#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-GUI environments
import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline

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

        # Sort data by transaction ID (or you can sort by initiation time if available)
        sorted_pairs = sorted(zip(transaction_ids, latencies))
        x_vals, y_vals = zip(*sorted_pairs)

        # Convert to numpy arrays
        x_vals = np.array(x_vals)
        y_vals = np.array(y_vals)

        # Create a smoother set of x values for plotting the smooth curve
        x_smooth = np.linspace(x_vals.min(), x_vals.max(), 500)

        # Perform spline interpolation for smoothing
        spl = make_interp_spline(x_vals, y_vals, k=3)  # Cubic spline
        y_smooth = spl(x_smooth)

        # Plotting
        plt.figure(figsize=(12, 6))
        plt.plot(x_smooth, y_smooth, color='blue', label='Smoothed Latency Curve')
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