#!/usr/bin/env python3
import subprocess
import sys
import time
import csv
import signal
import psutil
from pynvml import *
import matplotlib.pyplot as plt
import threading

# -----------------------------
# 配置
# -----------------------------
interval = 0.1  # 采样间隔（秒）
command = sys.argv[1:]  # 命令行参数作为被监控命令

if not command:
    print("Usage: python command_monitor.py <command> [args...]")
    sys.exit(1)

# -----------------------------
# 初始化 NVIDIA
# -----------------------------
nvmlInit()
gpu_handle = nvmlDeviceGetHandleByIndex(0)

# -----------------------------
# 全局数据
# -----------------------------
times = []
cpu_usages = []
mem_usages = []
gpu_powers = []
gpu_mems = []

start_time = time.time()
stop_flag = False

# -----------------------------
# Ctrl+C 信号处理
# -----------------------------
def signal_handler(sig, frame):
    global stop_flag
    print("\nCtrl+C detected. Stopping sampling...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)

# -----------------------------
# 启动被监控命令
# -----------------------------
proc = subprocess.Popen(command)
pid = proc.pid
print(f"Monitoring command PID={pid}")

process = psutil.Process(pid)

# -----------------------------
# 采样线程
# -----------------------------
def sample():
    while not stop_flag:
        t = time.time() - start_time
        # CPU / RAM
        try:
            children = process.children(recursive=True)
            procs = [process] + children
            cpu = sum(p.cpu_percent(interval=None) for p in procs)
            mem = sum(p.memory_info().rss for p in procs) / 1024 / 1024  # MB
        except psutil.NoSuchProcess:
            break

        # GPU
        power = nvmlDeviceGetPowerUsage(gpu_handle) / 1000
        gpu_mem = nvmlDeviceGetMemoryInfo(gpu_handle).used / 1024 / 1024

        times.append(t)
        cpu_usages.append(cpu)
        mem_usages.append(mem)
        gpu_powers.append(power)
        gpu_mems.append(gpu_mem)

        time.sleep(interval)

# -----------------------------
# 启动采样线程
# -----------------------------
thread = threading.Thread(target=sample)
thread.start()

# -----------------------------
# 等待命令结束
# -----------------------------
try:
    proc.wait()
except KeyboardInterrupt:
    stop_flag = True

thread.join()

# -----------------------------
# 保存 CSV
# -----------------------------
with open("monitor_stats.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_s", "cpu_%", "mem_MB", "gpu_power_W", "gpu_mem_MB"])
    for t, cpu, mem, pw, gm in zip(times, cpu_usages, mem_usages, gpu_powers, gpu_mems):
        writer.writerow([t, cpu, mem, pw, gm])

# -----------------------------
# 绘制两张子图，每个子图双 y 轴
# -----------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# -------- CPU / 内存 双轴 --------
ax1_left = ax1
ax1_right = ax1.twinx()

ax1_left.plot(times, cpu_usages, color="tab:blue", label="CPU %")
ax1_right.plot(times, mem_usages, color="tab:orange", label="RAM MB")

ax1_left.set_xlabel("Time (s)")
ax1_left.set_ylabel("CPU %", color="tab:blue")
ax1_right.set_ylabel("RAM MB", color="tab:orange")

ax1_left.tick_params(axis='y', labelcolor="tab:blue")
ax1_right.tick_params(axis='y', labelcolor="tab:orange")
ax1_left.grid(True)

# 图例合并
lines, labels = ax1_left.get_legend_handles_labels()
lines2, labels2 = ax1_right.get_legend_handles_labels()
ax1_left.legend(lines + lines2, labels + labels2, loc='upper right')
ax1.set_title("CPU and Memory Usage")

# -------- GPU 功率 / 显存 双轴 --------
ax2_left = ax2
ax2_right = ax2.twinx()

ax2_left.plot(times, gpu_powers, color="tab:blue", label="GPU Power (W)")
ax2_right.plot(times, gpu_mems, color="tab:orange", label="GPU Memory (MB)")

ax2_left.set_xlabel("Time (s)")
ax2_left.set_ylabel("GPU Power (W)", color="tab:blue")
ax2_right.set_ylabel("GPU Memory (MB)", color="tab:orange")

ax2_left.tick_params(axis='y', labelcolor="tab:blue")
ax2_right.tick_params(axis='y', labelcolor="tab:orange")
ax2_left.grid(True)

# 图例合并
lines, labels = ax2_left.get_legend_handles_labels()
lines2, labels2 = ax2_right.get_legend_handles_labels()
ax2_left.legend(lines + lines2, labels + labels2, loc='upper right')
ax2.set_title("GPU Power and Memory Usage")

plt.tight_layout()
plt.savefig("monitor_usage.png", dpi=200)
plt.close()

print("Saved: monitor_usage.png, monitor_stats.csv")
