#!/usr/bin/env python3

from mininet.node import Controller
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import os

# Define zones and their properties (only once at the top level)
zones = [
    {'id': 'z1', 'name': 'MMU', 'latency': '0ms'},
    {'id': 'z2', 'name': 'Monash', 'latency': '0.165ms'},
    {'id': 'z3', 'name': 'USIM', 'latency': '0.173ms'},
    {'id': 'z4', 'name': 'UKM', 'latency': '0.14ms'},
    {'id': 'z5', 'name': 'UPM', 'latency': '0.106ms'},
    # Add or remove zones and set their latencies here
]

class CosmosTopo(Topo):
    def __init__(self, zones, **opts):
        # Store zones before calling super().__init__()
        self.zones = zones
        super().__init__(**opts)

    def build(self):
        # Hub Switch
        hub_switch = self.addSwitch('s1')  # Cosmos Hub switch

        # Hub Nodes
        hv1 = self.addHost('hv1', ip='10.0.0.1/24')
        hv2 = self.addHost('hv2', ip='10.0.0.2/24')

        # Connect Hub Nodes to Hub Switch
        self.addLink(hv1, hub_switch)
        self.addLink(hv2, hub_switch)

        zone_switches = []
        for zone_info in self.zones:
            zone_id = zone_info['id']
            zone = zone_info['name']
            latency = zone_info['latency']
            i = int(zone_id[1:]) - 1

            zone_switch = self.addSwitch(f's{2+i}')  # Switches s2, s3, s4, etc.

            zone_val = self.addHost(f'{zone_id}_v1', ip=f'10.0.{i+1}.1/24')
            zone_full = self.addHost(f'{zone_id}_f1', ip=f'10.0.{i+1}.2/24')

            # Connect Zone Nodes to Zone Switch
            self.addLink(zone_val, zone_switch)
            self.addLink(zone_full, zone_switch)
            
            # Relayer Node for the Zone
            relayer = self.addHost(f'r{zone_id}')

            # Connect Relayer to both Hub Switch and Zone Switch with latency
            # Use zone IDs in interface names
            self.addLink(relayer, hub_switch, cls=TCLink, delay=latency,
                         intfName1=f'r{zone_id}-eth_hub', params1={'ip': None})
            self.addLink(relayer, zone_switch, cls=TCLink, delay=latency,
                         intfName1=f'r{zone_id}-eth_zone', params1={'ip': None})

            # Store zone switches for later use
            zone_switches.append(zone_switch)

        # Add controller node connected to all zone switches
        controller_node = self.addHost('controller')

        for i, zone_switch in enumerate(zone_switches):
            # Connect controller to each zone switch
            self.addLink(controller_node, zone_switch,
                         intfName1=f'controller-eth{i}', params1={'ip': None})

def run():
    # Use the global zones variable
    global zones

    topo = CosmosTopo(zones=zones)
    net = Mininet(topo=topo, controller=Controller, link=TCLink)
    net.start()

    # Get all nodes
    hv1 = net.get('hv1')
    hv2 = net.get('hv2')
    controller = net.get('controller')

    # Initialize nodes list
    nodes = [hv1, hv2, controller]

    for zone_info in zones:
        zone_id = zone_info['id']
        zone = zone_info['name']
        latency = zone_info['latency']
        i = int(zone_id[1:]) - 1

        relayer = net.get(f'r{zone_id}')

        # Assign IPs to Relayer interfaces using zone IDs
        relayer_intf_hub = relayer.intf(f'r{zone_id}-eth_hub')
        relayer_intf_zone = relayer.intf(f'r{zone_id}-eth_zone')

        relayer_ip_hub = f'10.0.0.{10 + i}/24'        # IP on Hub network
        relayer_ip_zone = f'10.0.{i+1}.10/24'         # IP on Zone network

        relayer_intf_hub.setIP(relayer_ip_hub)
        relayer_intf_zone.setIP(relayer_ip_zone)

        # Store relayer IPs for use in scripts if needed

        # Append zone nodes to nodes list
        zone_val = net.get(f'{zone_id}_v1')
        zone_full = net.get(f'{zone_id}_f1')
        nodes.extend([zone_val, zone_full, relayer])

    # Mount shared directory
    shared_dir = '/home/ubuntu/IBC_Simulation/mininet_shared'

    # Create logs directory in shared directory
    logs_dir = os.path.join(shared_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    for node in nodes:
        node.cmd(f'mkdir -p /home/ubuntu/IBC_Simulation/mininet_shared')
        node.cmd(f'mount --bind {shared_dir} /home/ubuntu/IBC_Simulation/mininet_shared')

    # Assign IP addresses to controller interfaces
    controller_intfs = controller.intfList()
    for i, intf in enumerate(controller_intfs):
        if intf.name != 'lo':
            # Assign IP on the corresponding zone network
            controller.setIP(f'10.0.{i+1}.200/24', intf=intf)

    # Start Cosmos Hub Nodes with logging
    hv1.cmd('python3 /home/ubuntu/IBC_Simulation/mininet_shared/hub_node.py hv1 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/hv1_log.txt 2>&1 &')
    hv2.cmd('python3 /home/ubuntu/IBC_Simulation/mininet_shared/hub_node.py hv2 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/hv2_log.txt 2>&1 &')

    # Start Zone Nodes and Relayers with logging
    for zone_info in zones:
        zone_id = zone_info['id']
        zone = zone_info['name']
        i = int(zone_id[1:]) - 1

        zone_val = net.get(f'{zone_id}_v1')
        zone_full = net.get(f'{zone_id}_f1')
        relayer = net.get(f'r{zone_id}')

        # Start Zone Validator Node
        zone_val.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/zone_node.py {zone_id}_v1 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/{zone_id}_v1_log.txt 2>&1 &')

        # Start Zone Full Node (modify as needed)
        zone_full.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/zone_node.py {zone_id}_f1 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/{zone_id}_f1_log.txt 2>&1 &')

        # Start Relayer Node
        relayer.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/relayer.py r{zone_id} "{zone}" > /home/ubuntu/IBC_Simulation/mininet_shared/logs/r{zone_id}_log.txt 2>&1 &')

    info('*** Simulation running. Use the Mininet CLI to interact.\n')

    # Display host information
    info('*** Hosts are as follows:\n')
    for host in net.hosts:
        info(f"    {host.name} - IP: {host.IP()}\n")
        # Display interface information
        for intf in host.intfList():
            if intf.name != 'lo':
                ip = host.IP(intf=intf)
                info(f"        {intf.name}: {ip}\n")

    # Start CLI for user interaction
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()