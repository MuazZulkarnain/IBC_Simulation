#!/usr/bin/env python3

import pandas as pd
import glob
import os

# Specify the folder containing the CSV files
folder_path = './Results/Medium/'  # Replace with the path to your folder

# Get a list of all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Check if any CSV files are found
if not csv_files:
    print("No CSV files found in the specified folder.")
else:
    # List to hold average DataFrames
    averages_list = []
    
    # Iterate over each CSV file
    for csv_file in csv_files:
        # Get just the file name without the path
        file_name = os.path.basename(csv_file)
        print(f"\nProcessing file: {file_name}")
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file)
        
        # List of columns to average (excluding 'run_id' which is not numeric)
        numeric_cols = df.columns.drop('run_id')
        
        # Convert columns to numeric, if they aren't already
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Compute the average of each numeric column
        averages = df[numeric_cols].mean()
        
        # Create a DataFrame from averages
        averages_df = averages.to_frame(name='Average').transpose()
        averages_df.insert(0, 'File', file_name)
        
        # Append to the list
        averages_list.append(averages_df)
        
    # Concatenate all averages into a single DataFrame
    summary_df = pd.concat(averages_list, ignore_index=True)
    
    # Define the output file path
    output_file = os.path.join(folder_path, 'summary_averages.csv')
    
    # Save the summary DataFrame to CSV
    summary_df.to_csv(output_file, index=False)
    print(f"\nSummary of averages saved to {output_file}")