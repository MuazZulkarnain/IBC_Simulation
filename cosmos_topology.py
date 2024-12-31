#!/usr/bin/env python3

from mininet.node import Controller, OVSKernelSwitch
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import os

class CosmosTopo(Topo):
    def build(self):
        # Cosmos Hub Switch
        hub_switch = self.addSwitch('s1')  # Cosmos Hub switch

        # Cosmos Hub Nodes
        hv1 = self.addHost('hv1', ip='10.0.0.1/24')
        hv2 = self.addHost('hv2', ip='10.0.0.2/24')

        # Connect Hub Nodes to Hub Switch
        self.addLink(hv1, hub_switch)
        self.addLink(hv2, hub_switch)

        # Zones
        zones = ['A', 'B', 'C']  # You can add more zones
        zone_switches = []
        for i, zone in enumerate(zones):
            zone_switch = self.addSwitch(f's{2+i}')  # Switches s2, s3, s4
            zone_val = self.addHost(f'z{zone.lower()}_v1', ip=f'10.0.{i+1}.1/24')
            zone_full = self.addHost(f'z{zone.lower()}_f1', ip=f'10.0.{i+1}.2/24')

            # Connect Zone Nodes to Zone Switch
            self.addLink(zone_val, zone_switch)
            self.addLink(zone_full, zone_switch)

            # Relayer Node for the Zone
            relayer = self.addHost(f'r{zone}')

            # Define latency based on distance
            if zone == 'A':
                latency = '2.5ms'
            elif zone == 'B':
                latency = '5ms'
            elif zone == 'C':
                latency = '7.5ms'

            # Connect Relayer to both Hub Switch and Zone Switch with latency
            self.addLink(relayer, hub_switch, cls=TCLink, delay=latency)
            self.addLink(relayer, zone_switch, cls=TCLink, delay=latency)

            # Store zone switches for later use
            zone_switches.append(zone_switch)

        # Add controller node connected to all zone switches
        controller_node = self.addHost('controller')

        for zone_switch in zone_switches:
            self.addLink(controller_node, zone_switch)

def run():
    topo = CosmosTopo()
    net = Mininet(topo=topo, controller=Controller, link=TCLink)
    net.start()

    # Get all nodes
    hv1 = net.get('hv1')
    hv2 = net.get('hv2')
    controller = net.get('controller')

    zones = ['A', 'B', 'C']
    relayer_ips = {}
    for i, zone in enumerate(zones):
        zone_label = zone
        zone_lower = zone.lower()
        zone_switch = net.get(f's{2+i}')
        zone_val = net.get(f'z{zone_lower}_v1')
        zone_full = net.get(f'z{zone_lower}_f1')
        relayer = net.get(f'r{zone}')

        # Assign IPs to Relayer interfaces
        relayer_intf_hub = relayer.intf(f'r{zone}-eth0')
        relayer_intf_zone = relayer.intf(f'r{zone}-eth1')

        relayer_ip_hub = f'10.0.0.{10 + i}/24'        # IP on Hub network
        relayer_ip_zone = f'10.0.{i+1}.10/24'         # IP on Zone network

        relayer_intf_hub.setIP(relayer_ip_hub)
        relayer_intf_zone.setIP(relayer_ip_zone)

        # Store relayer IPs for use in scripts
        relayer_ips[zone] = {
            'hub': relayer_ip_hub.split('/')[0],
            'zone': relayer_ip_zone.split('/')[0]
        }

    # Mount shared directory
    shared_dir = '/home/ubuntu/IBC_Simulation/mininet_shared'
    nodes = [hv1, hv2, controller]
    for zone in zones:
        nodes.extend([
            net.get(f'z{zone.lower()}_v1'),
            net.get(f'z{zone.lower()}_f1'),
            net.get(f'r{zone}')
        ])

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
    for i, zone in enumerate(zones):
        zone_label = zone
        zone_lower = zone.lower()
        zone_val = net.get(f'z{zone_lower}_v1')
        zone_full = net.get(f'z{zone_lower}_f1')
        relayer = net.get(f'r{zone}')

        # Start Zone Validator Node
        zone_val.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/zone_node.py z{zone_lower}_v1 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/z{zone_lower}_v1_log.txt 2>&1 &')

        # Start Zone Full Node (placeholder, modify as needed)
        zone_full.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/zone_node.py z{zone_lower}_f1 > /home/ubuntu/IBC_Simulation/mininet_shared/logs/z{zone_lower}_f1_log.txt 2>&1 &')

        # Start Relayer Node
        relayer.cmd(f'python3 /home/ubuntu/IBC_Simulation/mininet_shared/relayer.py r{zone_label} {zone_label} > /home/ubuntu/IBC_Simulation/mininet_shared/logs/r{zone_label}_log.txt 2>&1 &')

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