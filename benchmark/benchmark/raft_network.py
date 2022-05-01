import docker
import os

from contextlib import suppress
from docker import DockerClient
from docker.errors import DockerException
from .raft_helper import RaftHelper
from .raft_node import RaftNode


class RaftNetwork():
    def __init__(
        self,
        node_count,
        log_path,
        image,
        env_vars=[],
    ) -> None:
        self._node_count = node_count
        self._log_path = log_path
        self._image = image
        self._env_vars = env_vars
    
    def _create_network(self, docker_client: DockerClient):
        ipam_pool = docker.types.IPAMPool(
            subnet=RaftHelper.DOCKER_SUBNET,
            gateway=RaftHelper.DOCKER_GATEWAY,
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        try:
            docker_client.networks.create(
                RaftHelper.DOCKER_NETWORK,
                driver="bridge",
                ipam=ipam_config
            )
        except DockerException:
            pass
    
    def _spawn_nodes(self, docker_client: DockerClient):
        node_pool = []
        container_pool = []
        
        id_list = list(range(1, self._node_count + 1))
        for id in id_list:
            my_name = RaftHelper.get_node_name(id)
            my_cmd = RaftHelper.get_server_command(id, id_list)
            my_network = RaftHelper.DOCKER_NETWORK
            my_image = self._image
            my_port = RaftHelper.get_port(id)
            my_ports = {"8080/tcp": my_port}
            my_mounted_path = RaftHelper.get_mounted_log_path()
            my_log_path = os.path.join(my_mounted_path, f"{my_name}.log")
            my_volumes = {
                self._log_path.as_posix() : 
                    {
                        "bind": my_mounted_path,
                        "mode": "rw",
                    }
            }
            my_env_vars = [f"LOG_PATH={my_log_path}"]
            my_env_vars.extend(self._env_vars)
            raft_node = RaftNode(
                my_name, 
                [" ".join(my_cmd)], 
                my_image,
                my_network,
                my_ports,
                my_volumes,
                env_vars=my_env_vars,
            )
            container, err = raft_node.start(docker_client)
            if err != None:
                return None, err
            
            node_pool.append(raft_node)
            container_pool.append(container)
        return container_pool, None
            
    def start(self, docker_client: DockerClient):
        self._create_network(docker_client)
        node_pool, err = self._spawn_nodes(docker_client)
        if err != None:
            return None, err
        return node_pool, err

    @staticmethod
    def stop(container):
        container.stop()
            
    @staticmethod
    def stop_all(container_pool):
        for container in container_pool:
            RaftNetwork.stop(container)
    
    @staticmethod 
    def remove(container_pool):
        for container in container_pool:
            container.remove(v=True, force=True)
            
    @staticmethod 
    def slow_cpu(container, cpus: float = 0.1):
        cpu_period = 100000
        cpu_quota = int(cpu_period * cpus)
        with suppress(DockerException):
            container.update(cpu_period=cpu_period, cpu_quota=cpu_quota)

    @staticmethod
    def mem_contention(container, mem_limit = 10):
        with suppress(DockerException):
            container.update(mem_limit=f"{mem_limit}m", memswap_limit=f"{mem_limit+10}m")