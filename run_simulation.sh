#!/bin/bash

# Path to your Python script
Simulation_Script="/home/ubuntu/IBC_Simulation/cosmos_topology.py"

# Number of times to repeat the simulation
NUM_RUNS=2

# Loop to run the simulation
for (( run=1; run<=NUM_RUNS; run++ ))
do
    echo "Starting simulation run $run..."

    # Export an environment variable to be used by your Python script
    export RUN_NUMBER="$run"
    export RUN_DIR

    # Run the Python script, redirect output, and capture any errors
    python3 "$Simulation_Script"

    echo "Simulation run $run completed."
done

echo "All simulations completed."