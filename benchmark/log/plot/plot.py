import os
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

from ast import literal_eval

def plot_tl():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    with open(os.path.join(os.path.abspath(dir_path), "throughput_latency.txt"), "r") as data:
        str_list = data.read().split("\n")
        data_list = [s.split(": ")[1] for s in str_list if s]
        data_tuple = [literal_eval(d) for d in data_list if d]
        # data_tuple.sort(key = lambda e: e[1])
        print(data_tuple)
        
    with open(os.path.join(os.path.abspath(dir_path), "throughput_latency.txt"), "w+") as mod:
        for data in data_tuple:
            mod.write(f"(throughput, latency): {str(data)}\n")
        x = [x[0] for x in data_tuple]
        y = [x[1] for x in data_tuple]
        plt.plot(*zip(*data_tuple), marker='x', linewidth=0.5, markersize=1)
        # yhat = savgol_filter(y, len(x)//2+1, 5)
        # plt.plot(x,yhat, color='red')
        plt.xlabel('x - Throughput (RPS)')
        plt.ylabel('y - Delay(ns)')
        plt.title('Throughput Latency')
        plt.show()
        
def plot_latency():

    dir_path = os.path.dirname(os.path.realpath(__file__))
    rst = []
    with open(os.path.join(os.path.abspath(dir_path), "fault_latency_slow_cpu_leader.txt"), "r") as data:
        for d in data.read().split("\n"):
            try:
                rst.append(int(d))
            except ValueError:
                pass
    print(rst)
    plt.plot(list(range(len(rst))), rst, marker='x', linewidth=0.5, markersize=1)
    plt.xlabel('t - Time (sec)')
    plt.ylabel('y - Latency (ns)')
    plt.title('Latency')
    plt.show()
    plt.clf()
    
def plot_throughput():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    rst = []
    with open(os.path.join(os.path.abspath(dir_path), "fault_throughput*.txt"), "r") as data:
        for d in data.read().split("\n"):
            rst.append(int(d))
    plt.plot(list(range(len(rst))), rst, marker='x', linewidth=0.5, markersize=1)
    plt.xlabel('x - Request ID (x)')
    plt.ylabel('y - Throughput (RPnS)')
    plt.title('Throughput')
    plt.show()
    plt.clf()
    
def main():
    plot_tl()
    plot_latency()
    plot_throughput()
    
    
if __name__ == "__main__":
    main()