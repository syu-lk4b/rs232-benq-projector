# rs232-benq-projector

通过 **UETEL UE-E5410 双串口服务器 (RS232/RS485 over TCP)** 实现对 **明基 (BenQ) TK700 投影仪** 的局域网远程控制、命令行自动化以及 **Home Assistant / Apple HomeKit** 智能家居接入。

## 功能特性

- **RS232-over-TCP 透传控制**：通过 TCP Socket（默认端口 `8010`）直接收发明基标准 ASCII 控制指令（`115200-8-N-1`）。
- **零依赖 CLI 工具 (`tk700.py`)**：支持一键开关机、信号源切换（HDMI 1/2/3）、图像模式与灯泡节能模式切换、灯泡寿命及整机状态体检。
- **Home Assistant & HomeKit 完整接入**：支持 HACS `BenQ Projector` 集成（`socket://IP:8010`）及原生 `command_line` / `shell_command` 免插件配置。
- **完整协议与管理 API 文档**：详见 [`RS232.md`](./RS232.md)。

## 快速开始

### 1. 环境变量配置（可选）

```bash
export BENQ_HOST="192.168.5.40"
export BENQ_PORT="8010"
```

### 2. 使用 Python CLI 控制投影仪

```bash
# 查看整机实时状态
python3 tk700.py status

# 开关机
python3 tk700.py on
python3 tk700.py off

# 切换信号源
python3 tk700.py hdmi1
python3 tk700.py hdmi2

# 切换图像模式 / 灯泡模式
python3 tk700.py mode-hdr
python3 tk700.py mode-game
python3 tk700.py lamp-eco
python3 tk700.py lamp-normal

# 发送任意原生 RS232 指令
python3 tk700.py "ltim=?"
```

### 3. 使用 `nc` (Netcat) 一行命令控制

```bash
printf "\r*pow=?#\r"   | nc -w 1 192.168.5.40 8010
printf "\r*pow=on#\r"  | nc -w 1 192.168.5.40 8010
printf "\r*pow=off#\r" | nc -w 1 192.168.5.40 8010
```

## 详细文档

- [`RS232.md`](./RS232.md)：包含 UETEL UE-E5410 HTTP CGI 接口说明、BenQ TK700 完整 RS232 指令表、预热/冷却状态机说明及 Home Assistant 配置模板。
