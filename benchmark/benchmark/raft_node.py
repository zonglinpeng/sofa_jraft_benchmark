import docker
import atexit

from docker import DockerClient
from contextlib import suppress
from docker.models.containers import Container
from docker.errors import DockerException, NotFound


class RaftNode():
    def __init__(
        self,
        name,
        command,
        image,
        network,
        ports,
        volumes,
        env_vars=[],
    ) -> None:
        self._name = name
        self._command = command
        self._image = image
        self._network = network
        self._ports = ports
        self._volumes = volumes
        self._env_vars = env_vars
        
    def start(self, docker_client: DockerClient):
        print(self.__dict__)
        print()
        try:
            with suppress(NotFound):
                self.container: Container = docker_client.containers.run(
                    image=self._image,
                    name=self._name,
                    command=[*self._command],
                    network=self._network,
                    volumes=self._volumes,
                    ports={**self._ports},
                    environment=[*self._env_vars],
                    oom_kill_disable=True,
                    detach=True,
                )
        except DockerException as err:
            return None, err
        return self.container, None

    def stop(self):
        with suppress(NotFound):
            self.container.remove(force=True)