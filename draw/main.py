# main.py
import subprocess
import sys
import time

if __name__ == "__main__":
    # 启动监控子进程，传递命令行参数，--monitor和--namespace参数用于控制监控脚本的行为。确保monitor.py脚本的路径正确，或者在主程序中使用绝对路径。
    process = subprocess.Popen([sys.executable, "monitor.py", "--monitor", "--namespace", "default"])

    # 在此处添加您的压力测试代码
    time.sleep(30)

    # 等待压力测试完成
    process.wait()
    process.kill()

    # 获取监控子进程的输出
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        print("Monitoring completed successfully.")
    else:
        print(f"Monitoring failed with error: {stderr.decode()}")
