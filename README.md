# 监控命令资源占用

一个简单的 Python 脚本，用来在运行指定命令的同时采样 CPU、内存、GPU 功耗与显存，并输出曲线图和 CSV。

## 运行环境
- Python 3
- 依赖：`psutil`、`nvidia-ml-py`、`matplotlib`
- 需要具有 NVIDIA GPU 及已安装的 NVIDIA 驱动（提供 NVML 支持）

## 快速开始
```bash
pip install -r requirements.txt
python program_monitor.py <要执行的命令及参数>
```

示例：
```bash
python program_monitor.py python your_script.py --arg foo
```

## 输出
- `monitor_stats.csv`：时间序列数据，包含 `time_s,cpu_%,mem_MB,gpu_power_W,gpu_mem_MB`
- `monitor_usage.png`：两行子图，分别展示 CPU/内存 与 GPU 功耗/显存 的双轴曲线

## 说明
- 默认采样间隔 `0.1s`，可在脚本开头的 `interval` 变量调整。
- 运行时按 `Ctrl+C` 可停止采样并保存已采集的数据。

