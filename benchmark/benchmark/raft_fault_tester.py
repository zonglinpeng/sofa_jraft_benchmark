import os
from time import sleep
import matplotlib.pyplot as plt

from math import pow
from .raft_client import RaftClient
from .raft_network import RaftNetwork
from .raft_helper import RaftHelper
from .raft_log_parser import LogParser

class RaftFaultTestStarter:
    def __init__(
            self, 
            container_servers,
            sleep_interval,
            client_count, 
            raft_node_count,
            log_path,
            raft_node_image,
            plot_length = 100,
            test_size=int(pow(10,5)),
        ) -> None:
        self._container_servers = container_servers
        self._sleep_interval = sleep_interval
        self._client_count = client_count
        self._raft_node_count = raft_node_count
        self._log_path = log_path
        self._raft_node_image = raft_node_image
        self._plot_length = plot_length
        self._test_size = test_size
        self._logfile_name = ""
    
    def start_crash_leader(self, docker_client):
        self._logfile_name = "crash_leader"
        raft_client, client = self._start_client(docker_client)
        processor, throughput_monitor = self._start_monitor(client)
        RaftClient.wait_client(client)
        sleep(self._plot_length)
        server = RaftClient.get_leader_container(client, docker_client)
        RaftNetwork.stop(server)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)
        
    def start_crash_follower(self, docker_client):
        self._logfile_name = "crash_follower"
        raft_client, client = self._start_client(docker_client)
        processor, throughput_monitor = self._start_monitor(client)
        RaftClient.wait_client(client)
        sleep(self._plot_length)
        server = RaftClient.get_follower_container(client, docker_client)
        RaftNetwork.stop(server)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)
        
    def start_slow_cpu_leader_01(self, docker_client):
        cpus = float(0.1)
        self._logfile_name = "slow_cpu_leader"
        raft_client, client = self._start_client(docker_client)
        RaftClient.wait_client(client)
        processor, throughput_monitor = self._start_monitor(client)
        sleep(self._plot_length)
        server = RaftClient.get_leader_container(client, docker_client)
        RaftNetwork.slow_cpu(server, cpus)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)
    
    def start_slow_cpu_follower_01(self, docker_client):
        cpus = float(0.1)
        self._logfile_name = "slow_cpu_follower"
        raft_client, client = self._start_client(docker_client)
        RaftClient.wait_client(client)
        processor, throughput_monitor = self._start_monitor(client)
        sleep(self._plot_length)
        server = RaftClient.get_follower_container(client, docker_client)
        RaftNetwork.slow_cpu(server, cpus)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)
    
    def start_mem_contention_leader_10(self, docker_client):
        mem_limit = 10
        self._logfile_name = "mem_contention_leader"
        raft_client, client = self._start_client(docker_client)
        RaftClient.wait_client(client)
        processor, throughput_monitor = self._start_monitor(client)
        sleep(self._plot_length)
        server = RaftClient.get_leader_container(client, docker_client)
        RaftNetwork.mem_contention(server, mem_limit)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)
    
    def start_mem_contention_follower_10(self, docker_client):
        mem_limit = 10
        self._logfile_name = "mem_contention_follower"
        raft_client, client = self._start_client(docker_client)
        RaftClient.wait_client(client)
        processor, throughput_monitor = self._start_monitor(client)
        sleep(self._plot_length)
        server = RaftClient.get_follower_container(client, docker_client)
        RaftNetwork.mem_contention(server, mem_limit)
        sleep(self._plot_length)
        self._plot(raft_client, client, processor, throughput_monitor, self._logfile_name)

    def _start_client(self, docker_client):
        argv_pool = [str(self._client_count), str(self._sleep_interval), str(self._test_size), RaftHelper.get_mounted_log_path()]

        raft_client = RaftClient(
            self._raft_node_count,
            self._log_path,
            self._raft_node_image,
            name=f"{self._sleep_interval}{self._client_count}",
            client_count=self._client_count,
            cmd_argv=argv_pool,
        )
        client, err = raft_client.start(docker_client)
        if err != None:
            raise(err)
        return raft_client, client
    
    def _start_monitor(self, client):
        processor = RaftFaultLatencyProcessor(
            self._log_path, 
            self._container_servers, 
            client, 
            self._client_count * self._test_size - 1,
            self._logfile_name,
        )
        throughput_monitor = processor.start()
        return processor, throughput_monitor
               
    def _plot(self, raft_client, client, processor, throughput_monitor, log_name):  
        raft_client.stop(client)
        processor.load(throughput_monitor)
        processor.plot_latency(log_name)
        processor.plot_throughtput(log_name)
        raft_client.remove(client)
        
class RaftFaultLatencyProcessor:
    def __init__(self, log_path, servers, client, test_size, logfile_name) -> None:
        self._log_path = log_path
        self._latency_data = []
        self._throughput_data = []
        self._logfile_name = logfile_name
        self.raft_parser = LogParser(
            servers, 
            client, 
            test_size,
            self._log_path,
        )
    
    def start(self):
        throughput_monitor = self.raft_parser.monitor_fault_throughput(self._logfile_name)
        return throughput_monitor
    
    def load(self, throughput_monitor):
        latency_rst = self.raft_parser.parse_fault_latency(self._logfile_name)
        self._latency_data.extend(latency_rst)
        throughput = throughput_monitor.stop()
        self._throughput_data.extend(throughput)
        
    def plot_latency(self, name=""):
        plt.plot(list(range(len(self._latency_data))), self._latency_data, marker='x', linewidth=0.5, markersize=1)
        plt.xlabel('x - delta')
        plt.ylabel('y - Delay(ns)')
        plt.title('Fault Latency')
        plt.show()
        plt.savefig(f"fault_latency_{name}.png", bbox_inches="tight")
        plt.clf()
        
    def plot_throughtput(self, name=""):
        plt.plot(list(range(len(self._throughput_data))), self._throughput_data, marker='x', linewidth=0.5, markersize=1)
        plt.xlabel('x - delta')
        plt.ylabel('y - Throughput(PRnS)')
        plt.title('Fault Throughtput')
        plt.show()
        plt.savefig(f"fault_throughtput_{name}.png", bbox_inches="tight")
        plt.clf()