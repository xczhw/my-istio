import argparse
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import signal
import sys
import time

namespace = "test"  # 替换成您的命名空间

# 获取所有Pod的CPU和内存使用情况
def get_pod_metrics(namespace="default"):
    try:
        result = subprocess.run(
            ["kubectl", "top", "pod", "-n", namespace, "--no-headers"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.splitlines()
        pods = []
        for line in lines[1:]:
            columns = line.split()
            pod_name = columns[0]
            cpu_usage = columns[1]
            memory_usage = columns[2]
            pods.append([pod_name, cpu_usage, memory_usage])
        return pd.DataFrame(pods, columns=["Pod", "CPU Usage", "Memory Usage"])
    except subprocess.CalledProcessError as e:
        print("Error fetching pod resource usage:", e)
        return pd.DataFrame(columns=["Pod", "CPU Usage", "Memory Usage"])

# 画出CPU和内存使用情况图
def plot_resource_usage(pod_metrics):
    pod_metrics.set_index("Pod", inplace=True)
    pod_metrics["CPU Usage"] = pod_metrics["CPU Usage"].apply(lambda x: float(x[:-1]) if x.endswith("m") else 0)
    pod_metrics["Memory Usage"] = pod_metrics["Memory Usage"].apply(lambda x: float(x[:-2]) if x.endswith("Mi") else 0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    pod_metrics[["CPU Usage", "Memory Usage"]].plot(kind="bar", stacked=True, ax=ax)
    ax.set_xlabel("Pod")
    ax.set_ylabel("Resource Usage")
    ax.set_title("Pod CPU and Memory Usage")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("out/pod_resource_usage.png")
    plt.show()

def signal_handler(sig, frame):
    print("\nMonitoring interrupted. Exiting...")
    sys.exit(0)

# --monitor参数用于控制是否启用监控功能, signal_handler函数用于处理SIGINT和SIGTERM信号, 以便在接收到中断时退出监控循环
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Kubernetes Pod resource usage.")
    parser.add_argument('--namespace', type=str, default='default', help='Kubernetes namespace')
    parser.add_argument('--monitor', action='store_true', help='Enable resource monitoring')
    args = parser.parse_args()

    if args.monitor:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        print("Monitoring started. Press Ctrl+C to stop.")
        while True:
            pod_metrics = get_pod_metrics(args.namespace)
            if not pod_metrics.empty:
                plot_resource_usage(pod_metrics)
            else:
                print("No pod resource usage data found.")
            time.sleep(1)  # 每1秒更新一次
    else:
        print("Monitoring is disabled.")
