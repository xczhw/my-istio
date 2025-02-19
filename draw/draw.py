import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: 获取 caller pod
def get_caller_pod(namespace="default"):
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath={.items[*].metadata.name}"],
            capture_output=True, text=True, check=True
        )
        pods = result.stdout.split()
        for pod in pods:
            if "caller" in pod:
                return pod
    except subprocess.CalledProcessError as e:
        print("Error fetching pods:", e)
        return None
    return None

# Step 2: 获取 istio-proxy 日志
def get_envoy_logs(pod_name, namespace="default"):
    try:
        result = subprocess.run(
            ["kubectl", "logs", pod_name, "-c", "istio-proxy", "-n", namespace],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error fetching logs:", e)
        return ""

# Step 3: 解析日志
def parse_logs(logs):
    host_pattern = re.compile(r"\[RR LB\] Selected host: (\d+\.\d+\.\d+\.\d+:\d+)")
    host_count = {}

    for line in logs.splitlines():
        match = host_pattern.search(line)
        if match:
            host = match.group(1)
            host_count[host] = host_count.get(host, 0) + 1

    return host_count

# Step 4: 画出流量分布图
def plot_traffic_distribution(host_count):
    df = pd.DataFrame(list(host_count.items()), columns=["Host", "Request Count"])

    plt.figure(figsize=(10, 5))
    plt.bar(df["Host"], df["Request Count"])
    plt.xlabel("Host")
    plt.ylabel("Number of Requests")
    plt.title("Envoy Round Robin Load Balancing Traffic Distribution")
    plt.xticks(rotation=45)
    plt.savefig("out/traffic_distribution.png")

# 执行流程
namespace = "test"  # 替换成你的命名空间
caller_pod = get_caller_pod(namespace)

if caller_pod:
    print(f"Found caller pod: {caller_pod}")
    logs = get_envoy_logs(caller_pod, namespace)
    if logs:
        host_count = parse_logs(logs)
        print("Traffic Distribution:", host_count)
        plot_traffic_distribution(host_count)
    else:
        print("No logs found.")
else:
    print("Caller pod not found.")

# Step 1: 获取所有Pod的资源使用情况
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

# Step 2: 画出CPU和内存使用情况图
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

# 执行流程
namespace = "test"  # 替换成您的命名空间
pod_metrics = get_pod_metrics(namespace)

if pod_metrics:
    plot_resource_usage(pod_metrics)
else:
    print("No pod metrics found.")
