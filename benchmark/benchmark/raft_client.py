from time import sleep
import docker
import os
import regex as re

from docker import DockerClient
from docker.errors import DockerException
from .raft_helper import RaftHelper
from .raft_node import RaftNode

class RaftClient:
    def __init__(
        self,
        node_count,
        log_path,
        image,
        name = "self",
        port_delta = 0,
        client_count = 1,
        cmd_argv=[],
        env_vars=[],
    ) -> None:
        self._node_count = node_count
        self._client_id = node_count + 1
        self._log_path = log_path
        self._image = image
        self._name = name
        self._port_delta = port_delta
        self._client_count = client_count
        self._cmd_argv = cmd_argv
        self._env_vars = env_vars
    
    def start(self, docker_client: DockerClient):
        id_list = list(range(1, self._node_count + 1))
        my_name = RaftHelper.get_client_name(self._name)
        my_cmd = RaftHelper.get_multi_client_command(id_list, self._cmd_argv)
        my_network = RaftHelper.DOCKER_NETWORK
        my_image = self._image
        my_port = RaftHelper.get_port(self._client_id + self._port_delta)
        my_ports = {"8080/tcp": my_port}
        my_mounted_path = RaftHelper.get_mounted_log_path()
        my_volumes = {
            self._log_path.as_posix() : 
                {
                    "bind": my_mounted_path,  # TODO ?
                    "mode": "rw",
                }
        }
        raft_node = RaftNode(
            my_name, 
            [" ".join(my_cmd)], 
            my_image,
            my_network,
            my_ports,
            my_volumes,
            env_vars=self._env_vars,
        )
        container, err = raft_node.start(docker_client)
        if err != None:
            return None, err
        
        return container, None
    
    @staticmethod
    def stop(container):
        container.stop()
        
    @staticmethod  
    def remove(container):
        container.remove(v=True, force=True)
    
    @staticmethod
    def wait_client(container):
        while "Leader is" not in container.logs().decode(): sleep(1)
            
    @staticmethod
    def get_leader_container(container, docker_client: DockerClient):
        logs = container.logs().decode().split("\n")
        for line in logs:
            if "Leader is" in line:
                ip = re.compile("Leader is (.*$)").search(line).group(1)
                name = RaftHelper.get_node_name_from_ip(ip)
                return docker_client.containers.get(name)
        print("No leader is found")
    
    @staticmethod
    def get_follower_container(container, docker_client: DockerClient):
        logs = container.logs().decode().split("\n")
        for line in logs:
            if "Leader is" in line:
                ip = re.compile("Leader is (.*$)").search(line).group(1)
                name = RaftHelper.get_node_name_from_ip(ip)
        for container in docker_client.containers.list():
            my_name = container.stats(stream=False)["name"]
            if "client" not in my_name and name not in my_name:
                return container
                
    