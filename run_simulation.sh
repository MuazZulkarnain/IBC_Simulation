#!/bin/bash

# Path to your Mininet script
MININET_SCRIPT="./cosmos_topology.py"

# Parameters for your simulations
TEST_DURATION="10"        # Test duration in seconds
TPS="1000"                # Transactions per second

# Start Mininet in the background
sudo python3 $MININET_SCRIPT &
MININET_PID=$!

# Give Mininet some time to start (adjust as necessary)
echo "Waiting for Mininet to start..."
sleep 10

# Run the simulation controller inside the Mininet 'controller' node
echo "Running simulation with duration=$TEST_DURATION and tps=$TPS"

sudo python3 -m mininet.node -c controller python3 /home/ubuntu/IBC_Simulation/mininet_shared/simulation_controller.py --duration $TEST_DURATION --tps $TPS

# Wait for the simulation to complete
echo "Simulation running..."
sleep $((TEST_DURATION + 5))

# After simulations, stop Mininet
echo "Stopping Mininet..."
sudo kill $MININET_PID
sudo mn -c

echo "Simulations completed."