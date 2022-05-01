import os
import matplotlib.pyplot as plt

from .raft_client import RaftClient
from .raft_helper import RaftHelper
from .raft_log_parser import LogParser
from datetime import datetime
from typing import List
from docker import DockerClient
from docker.models.containers import Container
from time import sleep


class RaftLoadTestStarter:
    def __init__(
        self, 
        container_servers,
        max_sleep, 
        max_client, 
        load,
        raft_node_count,
        log_path,
        raft_node_image,
        test_size,
    ) -> None:
        self._container_servers = container_servers
        self._max_sleep = max_sleep
        self._max_client = max_client
        self._load = load
        self._raft_node_count = raft_node_count
        self._log_path = log_path
        self._raft_node_image = raft_node_image
        self._test_size = test_size
    
    @staticmethod
    def _is_completed(container: Container, client_count):
        counter = 0
        logs = container.logs().decode().split("\n")
        for log in logs:
            if "DONE" in log:
                counter += 1
        return client_count == counter
            
    def start(self, docker_client: DockerClient):
        processor = RaftThroughputLatencyProcessor(self._log_path)
        for sleep_t in range(self._max_sleep, -1, -10):
            for client_count in range(1, self._max_client + 1):
                argv_pool = [str(client_count), str(sleep_t), str(self._load), RaftHelper.get_mounted_log_path()]

                raft_client = RaftClient(
                    self._raft_node_count,
                    self._log_path,
                    self._raft_node_image,
                    name=f"{sleep_t}{client_count}",
                    client_count=client_count,
                    cmd_argv=argv_pool,
                )
                client, err = raft_client.start(docker_client)
                if err != None:
                    raise(err)
                
                while not RaftLoadTestStarter._is_completed(client, client_count): sleep(1)
                                
                processor.load(
                    self._container_servers, 
                    client, 
                    client_count * self._test_size - 1,
                )
                
                RaftClient.remove(client)
                
                sleep(1)
                
        processor.plot()
                
            
class RaftThroughputLatencyProcessor:
    def __init__(self, log_path) -> None:
        self._log_path = log_path
        self._data = []
    
    def load(self, servers, client, test_size):
        raft_parser = LogParser(
            servers, 
            client, 
            test_size,
            self._log_path,
        )
        t_l_pair = raft_parser.parse_throughput_latency()
        self._data.append(t_l_pair)
        
    def plot(self):
        self._data.sort(key=lambda x: x[0])
        plt.plot(*zip(*self._data), marker='x', linewidth=0.5, markersize=1)
        plt.show()
        plt.savefig("throughput_latency.png", bbox_inches="tight")
        