import regex as re

class RaftHelper:
    DOCKER_HOST = "192.168.52"
    DOCKER_SUBNET = "192.168.52.0/24"
    DOCKER_GATEWAY = "192.168.52.254"
    DOCKER_NETWORK = "raft_network"
    
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def get_mounted_log_path():
        return "/tmp/"
    
    @staticmethod
    def get_node_name(id):
        return f"raft_node_{id}"
    
    @staticmethod
    def get_node_name_from_ip(addr):
        id = re.compile("192.168.52.(.*?):8080").search(addr).group(1)
        return RaftHelper.get_node_name(id)
    
    @staticmethod
    def get_client_name(id):
        return f"raft_client_{id}"
    
    @staticmethod
    def get_port(id):
        return int(8080 + id)

    @staticmethod
    def get_ip_addr(id):
        return f"{RaftHelper.DOCKER_HOST}.{id}"

    @staticmethod
    def get_self_addr(id):
        return f"{RaftHelper.get_ip_addr(id)}:8080"
           
    @staticmethod     
    def get_cluster_addr(id_list):
        addr_list = [RaftHelper.get_self_addr(id) for id in id_list]
        return ",".join(addr_list)
    
    @staticmethod
    def get_server_command(id, id_list):
        return [
            "java", 
            "-cp", 
            "'*'",
            "com.alipay.sofa.jraft.example.counter.CounterServer",
            f"/tmp/server{id}", 
            "counter",
            RaftHelper.get_self_addr(id),
            RaftHelper.get_cluster_addr(id_list),
        ]
        
    @staticmethod
    def get_client_command(id_list):
        return [
            "java", 
            "-cp", 
            "'*'",
            "com.alipay.sofa.jraft.example.counter.CounterClient",
            "counter",
            RaftHelper.get_cluster_addr(id_list),
        ]
        
    @staticmethod
    def get_multi_client_command(id_list, argv):
        # rst_command = []
        # for _ in range(count):
        #     rst_command.extend(RaftHelper.get_client_command(id_list) + argv.pop(0))
        # rst_command.extend(RaftHelper.get_client_command(id_list) + argv)
        # return rst_command
        
        return RaftHelper.get_client_command(id_list) + argv
