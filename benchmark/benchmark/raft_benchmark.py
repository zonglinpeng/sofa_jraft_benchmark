import logging
import docker
import os
import shutil

from contextlib import suppress
from time import sleep
from pathlib import Path
from .raft_network import RaftNetwork
from .raft_load_tester import RaftLoadTestStarter
from .raft_fault_tester import RaftFaultTestStarter


logger = logging.getLogger(__name__)

class Benchmark:
    def __init__(
        self,
        raft_node_count,
        raft_node_image,
        raft_client_image,
        raft_load_gen_image,
        raft_test_size,
        raft_max_sleep,
        raft_max_n,
        raft_load,
        log_path,
    ) -> None:
        self._docker_client = docker.from_env()
        self._raft_node_count = raft_node_count
        self._raft_node_image = raft_node_image
        self._raft_client_image = raft_client_image
        self._raft_load_gen_image = raft_load_gen_image
        self._raft_test_size = raft_test_size
        self._raft_max_sleep = raft_max_sleep
        self._raft_max_n = raft_max_n
        self._raft_load = raft_load
        self._log_path = Path(os.path.abspath(log_path))
        
    def start(self):
        raft_network = RaftNetwork(
            self._raft_node_count,
            self._log_path,
            self._raft_node_image
        )
        servers, err = raft_network.start(self._docker_client)
        if err != None:
            raise(err)
        
        load_test = RaftLoadTestStarter(
            container_servers=servers,
            max_sleep=self._raft_max_sleep,
            max_client=self._raft_max_n,
            load=self._raft_load,
            raft_node_count=self._raft_node_count,
            log_path=self._log_path,
            raft_node_image=self._raft_node_image,
            test_size=self._raft_test_size,
        )
        load_test.start(self._docker_client)

        fault_test = RaftFaultTestStarter(
            container_servers=servers,
            sleep_interval=self._raft_max_sleep,
            client_count=self._raft_max_n,
            raft_node_count=self._raft_node_count,
            log_path=self._log_path,
            raft_node_image=self._raft_node_image,
        )
        
        fault_test.start_crash_leader(self._docker_client)
        fault_test.start_crash_follower(self._docker_client)
        fault_test.start_slow_cpu_leader_01(self._docker_client)
        fault_test.start_slow_cpu_follower_01(self._docker_client)
        fault_test.start_mem_contention_leader_10(self._docker_client)
        fault_test.start_mem_contention_follower_10(self._docker_client)
        
        
def main():
    raft_node_count = 5 
    raft_node_image = "zonglin7/raft:dev"
    raft_client_image = None
    raft_load_gen_image = None
    raft_test_size = 2000 # 10000
    raft_max_sleep = 10 # 100
    raft_max_n = 40 # 2
    raft_load = raft_test_size
    log_path = "./tmp"
    
    with suppress(FileNotFoundError):
        shutil.rmtree(log_path)
    
    benchmark = Benchmark(
        raft_node_count,
        raft_node_image,
        raft_client_image,
        raft_load_gen_image,
        raft_test_size,
        raft_max_sleep,
        raft_max_n,
        raft_load,
        log_path,
    )
    
    benchmark.start()

if __name__ == "__main__":
    main()