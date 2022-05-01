import regex as re
import json
import glob
import os
import threading
from dateutil.parser import parse
from dateutil.parser._parser import ParserError

from time import sleep
from contextlib import suppress
from threading import Thread
from statistics import quantiles
from typing import List
from docker.models.containers import Container

class LogParser:
    def __init__(
        self, 
        servers: List[Container], 
        client: Container,
        test_size,
        log_path,
    ) -> None:
        self._servers = servers
        self._client = client
        self._test_size = test_size
        self._log_path = log_path
    
    @staticmethod
    def _reset_log(path):
        open(path, "w").close
    
    def _reset_all_log(self):
        for fpath in glob.glob(os.path.join(self._log_path, "raft_node*log")):
            LogParser._reset_log(fpath)
        for fpath in glob.glob(os.path.join(self._log_path, "raft_client*log")):
            LogParser._reset_log(fpath)
            
    def _parse_servers_latency(self, log_pool):
        latency = []
        for fpath in glob.glob(os.path.join(self._log_path, "raft_node*log")):
            with open(fpath, "r") as log_file:
                logs = log_file.read().split("\n")
                for log in logs:
                    matches = re.findall(r"RAFT_END(.*$)", log)
                    for string in matches:
                        delta_list = json.loads(string)["deltaList"]
                        time = int(json.loads(string)["time"])
                        for delta in delta_list:
                            try:
                                if log_pool[delta] == -1:
                                    continue
                                latency.append(time - log_pool[delta])
                            except KeyError:
                                print(f"delta {delta} does not exist!!")
                            except IndexError:
                                print(f"delta {delta} outta range!!")
        print(len(log_pool), len(latency))
        return latency
        
    def _parse_client_latency(self, log_pool):
        for fpath in glob.glob(os.path.join(self._log_path, "raft_client*log")):
            with open(fpath, "r") as log_file:
                logs = log_file.read().split("\n")
                for log in logs:
                    matches = re.findall(r"RAFT_START(.*$)", log)
                    for string in matches:
                        delta = int(json.loads(string)["delta"])
                        time = int(json.loads(string)["time"])
                        try:
                            log_pool[delta] = time
                        except KeyError:
                            print(f"delta {delta} does not exist!!")
                        except IndexError:
                            print(f"delta {delta} outta range!!")
            
    def _parse_client_throughput(self):
        throughput = float(0)
        for fpath in glob.glob(os.path.join(self._log_path, "raft_client*log")):
            with open(fpath, "r") as log_file:
                logs = log_file.read().split("\n")
                for log in logs:
                    matches = re.findall(r"RAFT_THROUGHPUT(.*$)", log)
                    for string in matches:
                        throughput += float(json.loads(string)["throughput"])
        return throughput
    
    @staticmethod
    def calculate_p50(latency):
        return quantiles(latency, n=100)[49]
        
    def parse_throughput_latency(self):
        latency_pool = [-1 for _ in range (self._test_size)]
        self._parse_client_latency(latency_pool)
        latency_rst = self._parse_servers_latency(latency_pool)
        
        throughput = self._parse_client_throughput()
        latency = LogParser.calculate_p50(latency_rst)
        
        data = f"(throughput, latency): ({throughput}, {latency})\n"
        with open(os.path.join(self._log_path, "throughput_latency.txt"), "a") as myfile:
            myfile.write(data)
            
        self._reset_all_log()
        
        return (throughput, latency)
        
    def parse_fault_latency(self, logfile_name=""):
        latency_pool = [-1 for _ in range (self._test_size)]
        self._parse_client_latency(latency_pool)
        latency_rst = self._parse_servers_latency(latency_pool)
        with suppress(ValueError):
            latency_rst.remove(-1)
        with open(os.path.join(self._log_path, f"fault_latency_{logfile_name}.txt"), "a") as myfile:
            for latency in latency_rst:
                myfile.write(f"{str(latency)}\n")
            
        self._reset_all_log()
        return latency_rst
    
    def monitor_fault_throughput(self, logfile_name=""):
        throughput_monitor = ThroughputMonitor(self._client, self._log_path, logfile_name)
        throughput_monitor.start()
        return throughput_monitor
    
    def parse_fault_throughput(container):
        self._container.logs().decode()
    
class ThroughputMonitor:
    def __init__(self, container, log_path, logfile_name) -> None:
        self._container = container
        self._log_path = log_path
        self._logfile_name = logfile_name
        self._quit = threading.Event()
        self._throughputs = []

    def _main(self) -> None:
        prev_time = None
        success_count = 0
        for log in self._container.logs(timestamps=True, stream=True):
            if self._quit.is_set():
                return
            log = log.decode()
            if "success: true" in log:
                success_count += 1
            
            try:
                time = log.split(" ")[0]
            except KeyError:
                continue
            try:
                cur_datetime = parse(time)
            except ParserError:
                continue
            if prev_time is None:
                prev_time = cur_datetime
            if (cur_datetime - prev_time).total_seconds() >= 1:
                self._throughputs.append(success_count)
                success_count = 0
                prev_time = cur_datetime

    def start(self) -> None:
        t = Thread(target=self._main, args=(), daemon=True)
        t.start()

    def stop(self):
        self._quit.set()
        with open(os.path.join(self._log_path, f"fault_throughtput_{self._logfile_name}.txt"), "a") as myfile:
            for thru in self._throughputs:
                myfile.write(f"{str(thru)}\n")
        return self._throughputs
