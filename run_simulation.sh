#!/bin/bash

# Path to your Python script
Simulation_Script="/home/ubuntu/IBC_Simulation/cosmos_topology.py"

# Number of times to repeat the simulation
NUM_RUNS=50

# Loop to run the simulation
for (( run=1; run<=NUM_RUNS; run++ ))
do
    echo ""
    echo ""
    echo "##############################"
    echo "Starting simulation run $run..."
    echo "##############################"    

    # Export an environment variable to be used by your Python script
    export RUN_NUMBER="$run"
    export RUN_DIR

    # Run the Python script, redirect output, and capture any errors
    sudo python3 "$Simulation_Script"

    echo ""
    echo ""
    echo "##############################"
    echo "Simulation run $run completed."
    echo "##############################" 

    python3 ./mininet_shared/calculate_latency.py
    sudo rm -rf ./mininet_shared/logs
    mkdir ./mininet_shared/logs
done

echo ""
echo ""
echo "##############################"  
echo "All simulations completed."
echo "##############################"  