# rs232-benq-projector

[中文说明](#-中文说明) | [English](#-english)

---

## 📖 中文说明

通过 **UETEL UE-E5410 双串口服务器 (RS232/RS485 over TCP)** 实现对 **明基 (BenQ) TK700 投影仪** 的局域网远程控制、命令行自动化，以及 **Home Assistant** 与 **Apple HomeKit（家庭 App / Siri）** 智能家居完整接入。

### 1. 系统架构与工作原理

```text
[Apple 家庭 App / Siri]
         │ (HomeKit Bridge - TV Accessory Mode)
         ▼
[Home Assistant]  或  [CLI (tk700.py / nc)]
         │ (TCP Socket: 192.168.5.40:8010)
         ▼
[UETEL UE-E5410 串口服务器] (Port 1: TCPS -> UART1 115200-8-N-1)
         │ (RS232 DB9 串口线)
         ▼
[明基 BenQ TK700 投影仪] (ASCII 协议: \r*<cmd>=<val>#\r)
```

### 2. 串口服务器配置 (UETEL UE-E5410)

在串口服务器 Web 后台（或通过 CGI 接口）将 **端口 1 (RS232)** 配置为 TCP Server 透传模式：

| 配置项 | 参数值 | 说明 |
| :--- | :--- | :--- |
| **波特率 / 数据位 / 停止位 / 校验** | `115200` / `8` / `1` / `NONE` | 明基 TK700 默认串口参数 |
| **流控 (`fc`)** | `NFC` | 无流控 |
| **分包间隔 / 长度** | `5 ms` / `1024 Bytes` | 保证 ASCII 响应帧完整打包 |
| **Socket 1A 开关 / 协议** | `ON` / `TCPS` (TCP Server) | 允许局域网客户端主动连接 |
| **Socket 1A 本地监听端口** | `8010` | 最多支持 8 个客户端并发连接 |

---

### 3. 本地 CLI 与命令行快速控制

#### 使用零依赖 Python 工具 `tk700.py`

```bash
# 可选：通过环境变量覆盖默认地址与端口 (默认 192.168.5.40:8010)
export BENQ_HOST="192.168.5.40"
export BENQ_PORT="8010"

# 一键查询投影仪完整状态（型号、电源、信号源、图像模式、灯泡模式与寿命等）
python3 tk700.py status

# 电源控制
python3 tk700.py on
python3 tk700.py off

# 切换 HDMI 输入源
python3 tk700.py hdmi1
python3 tk700.py hdmi2
python3 tk700.py hdmi3

# 切换图像模式与灯泡节能模式
python3 tk700.py mode-hdr
python3 tk700.py mode-game
python3 tk700.py mode-cinema
python3 tk700.py lamp-eco
python3 tk700.py lamp-normal

# 发送任意原生明基 RS232 指令
python3 tk700.py "ltim=?"
```

#### 使用 `nc` (Netcat) 一行命令控制

```bash
printf "\r*pow=?#\r"     | nc -w 1 192.168.5.40 8010   # 查询电源
printf "\r*pow=on#\r"    | nc -w 1 192.168.5.40 8010   # 开机
printf "\r*pow=off#\r"   | nc -w 1 192.168.5.40 8010   # 关机
printf "\r*sour=hdmi#\r" | nc -w 1 192.168.5.40 8010   # 切 HDMI 1
printf "\r*sour=hdmi2#\r"| nc -w 1 192.168.5.40 8010   # 切 HDMI 2
```

---

### 4. Home Assistant 接入配置

支持 **HACS UI 集成（推荐）** 和 **原生 `configuration.yaml` 配置** 两种方式。

#### 方式 A：通过 HACS `BenQ Projector` 集成（推荐，支持完整 `media_player` 电视实体）

适用于所有 Home Assistant 安装方式（包括无文件编辑器加载项的 Docker Container 环境）：

1. **安装插件**：在 **HACS -> 集成 (Integrations)** 中搜索并下载 **`BenQ Projector`**（仓库：`rrooggiieerr/homeassistant-benqprojector`），然后重启 Home Assistant。
2. **添加集成**：进入 **设置 -> 设备与服务 -> 添加集成 -> 搜索 `BenQ Projector`**。
3. **填写连接参数**：
   - **连接类型**：选择 **Network / Serial over IP**
   - **Host / 地址**：`192.168.5.40`
   - **Port / 端口**：`8010`
   - **Baudrate / 波特率**：`115200`（如插件自动协商则无需手填）
4. **生成的实体**：
   - 主实体：`media_player.benq_tk700`（`device_class: tv`，支持电源开关、HDMI 输入源切换、音量/静音）
   - 附属实体：灯泡使用时长 (`sensor.*_lamp_time`)、图像模式 (`select.*_picture_mode`)、灯泡模式 (`select.*_lamp_mode`)、画面黑屏遮罩 (`switch.*_blank`) 等。

#### 方式 B：原生 `configuration.yaml` 免插件配置

如果不使用 HACS，可将以下配置直接加入 Home Assistant 的 `configuration.yaml`：

```yaml
command_line:
  # 1. 投影仪电源开关
  - switch:
      name: "BenQ TK700 Projector"
      unique_id: benq_tk700_power
      icon: mdi:projector
      command_on: 'printf "\r*pow=on#\r" | nc -w 2 192.168.5.40 8010'
      command_off: 'printf "\r*pow=off#\r" | nc -w 2 192.168.5.40 8010'
      command_state: 'printf "\r*pow=?#\r" | nc -w 2 192.168.5.40 8010 | tr -d "\r\n"'
      value_template: '{{ "*POW=ON#" in value }}'
      scan_interval: 15

  # 2. 画面遮罩 (Blank) 开关
  - switch:
      name: "TK700 Blank Screen"
      unique_id: benq_tk700_blank
      icon: mdi:eye-off
      command_on: 'printf "\r*blank=on#\r" | nc -w 2 192.168.5.40 8010'
      command_off: 'printf "\r*blank=off#\r" | nc -w 2 192.168.5.40 8010'
      command_state: 'printf "\r*blank=?#\r" | nc -w 2 192.168.5.40 8010 | tr -d "\r\n"'
      value_template: '{{ "*BLANK=ON#" in value }}'
      scan_interval: 30

  # 3. 灯泡累计使用时间传感器
  - sensor:
      name: "TK700 Lamp Hours"
      unique_id: benq_tk700_lamp_hours
      icon: mdi:lightbulb-clock
      unit_of_measurement: "h"
      command: 'printf "\r*ltim=?#\r" | nc -w 2 192.168.5.40 8010 | tr -d "\r\n"'
      value_template: >
        {% set m = value | regex_findall_index('\*LTIM=([0-9]+)#', ignorecase=True) %}
        {{ m if m else this.state }}
      scan_interval: 300

  # 4. 当前输入信号源传感器
  - sensor:
      name: "TK700 Source"
      unique_id: benq_tk700_source
      icon: mdi:video-input-hdmi
      command: 'printf "\r*sour=?#\r" | nc -w 2 192.168.5.40 8010 | tr -d "\r\n"'
      value_template: >
        {% if '*SOUR=HDMI2#' in value %}HDMI 2
        {% elif '*SOUR=HDMI3#' in value %}HDMI 3
        {% elif '*SOUR=HDMI#' in value %}HDMI 1
        {% else %}Unknown{% endif %}
      scan_interval: 15

shell_command:
  tk700_hdmi1: 'printf "\r*sour=hdmi#\r" | nc -w 2 192.168.5.40 8010'
  tk700_hdmi2: 'printf "\r*sour=hdmi2#\r" | nc -w 2 192.168.5.40 8010'
  tk700_lamp_normal: 'printf "\r*lampm=lnor#\r" | nc -w 2 192.168.5.40 8010'
  tk700_lamp_eco: 'printf "\r*lampm=eco#\r" | nc -w 2 192.168.5.40 8010'
  tk700_mode_hdr: 'printf "\r*appmod=hdr#\r" | nc -w 2 192.168.5.40 8010'
  tk700_mode_game: 'printf "\r*appmod=game#\r" | nc -w 2 192.168.5.40 8010'
  tk700_mode_cinema: 'printf "\r*appmod=cine#\r" | nc -w 2 192.168.5.40 8010'
```

---

### 5. Apple HomeKit 集成配置（Siri / 家庭 App 电视配件）

为了让投影仪在 iPhone / iPad / Mac 的「家庭 (Home)」App 中以原生 **电视 (TV) 配件** 呈现（支持开关机、在家庭 App 内下拉切换 HDMI 1/2 输入源、使用 iPhone 控制中心遥控器以及 Siri 语音控制），需在 Home Assistant 中使用 **Accessory Mode（单配件模式）** 桥接 `media_player.benq_tk700`：

#### 方式 A：通过 Home Assistant UI 配置 HomeKit Bridge

1. 确保 `media_player.benq_tk700` 实体的设备类别（Show as / `device_class`）为 **`tv`（电视）**。
2. 进入 **设置 -> 设备与服务 -> 添加集成 -> 搜索 `HomeKit Bridge`**。
3. 在弹出的配置向导中：
   - **包含的域 (Domains to include)**：勾选 **`Media Player`（媒体播放器）**。
   - **桥接模式 (HomeKit Mode)**：选择 **`accessory`（单配件模式）**（⚠️ 关键：Apple HomeKit 规范要求电视类 `media_player` 必须以独立 `accessory` 模式导出，不能混在普通 `bridge` 桥接器中）。
   - **目标实体 (Entity)**：选择 **`media_player.benq_tk700`（明基投影仪）**。
4. 提交后，在 Home Assistant「通知」中会出现该电视配件专属的 **HomeKit 配对二维码 / 8 位配对码**。
5. 打开 iPhone「家庭」App -> 右上角 `+` -> **添加配件** -> 扫描二维码即可完成添加。
   > **提示**：如果在现有的 Bridge 配置流里勾选了整个 `media_player` 域，HA 会自动为域内每台电视额外新建独立的 accessory 实例，如果出现多余实例手动删除即可。

#### 方式 B：通过 `configuration.yaml` 配置 HomeKit 电视配件

```yaml
homeassistant:
  customize:
    media_player.benq_tk700:
      device_class: tv
      friendly_name: "明基投影仪"

homekit:
  - name: "HomeKit-明基投影仪"
    port: 21065
    mode: accessory
    filter:
      include_entities:
        - media_player.benq_tk700
```

#### 状态机与实测注意事项（预热期与散热期）

- **开机预热期（约 40 秒）**：发送开机指令后，灯泡处于点亮预热阶段，此时发送关机指令会被投影仪硬件忽略（返回 `*Block item#`）；需等待约 40 秒画面出现信号源后才能执行关机或切源。
- **关机散热期（约 90 秒）**：发送关机指令后，投影仪进入风扇高速散热阶段，期间串口查询会返回 `*Block item#`。此时 Home Assistant 中实体会短暂显示为 `unavailable`，HomeKit 显示「无响应」；约 90 秒散热完成后自动恢复为 `off` 待机状态。

---

## 🌐 English

Control a **BenQ TK700 Projector** over LAN using a **UETEL UE-E5410 Dual Serial Server (RS232/RS485 over TCP)**, complete with a zero-dependency Python CLI and full **Home Assistant** & **Apple HomeKit (Home App / Siri)** integration.

### 1. Architecture

```text
[Apple Home App / Siri]
         │ (HomeKit Bridge - TV Accessory Mode)
         ▼
[Home Assistant]  or  [CLI (tk700.py / nc)]
         │ (TCP Socket: 192.168.5.40:8010)
         ▼
[UETEL UE-E5410 Serial Server] (Port 1: TCPS -> UART1 115200-8-N-1)
         │ (RS232 DB9 Cable)
         ▼
[BenQ TK700 Projector] (ASCII Protocol: \r*<cmd>=<val>#\r)
```

### 2. Serial Server Configuration (UETEL UE-E5410)

Configure **Port 1 (RS232)** on the UETEL UE-E5410 as a transparent TCP Server:

| Setting | Value | Description |
| :--- | :--- | :--- |
| **Baudrate / Databits / Stopbits / Parity** | `115200` / `8` / `1` / `NONE` | Default serial config for BenQ TK700 |
| **Flow Control (`fc`)** | `NFC` | No flow control |
| **Frame Interval / Length** | `5 ms` / `1024 Bytes` | Keeps ASCII response frames intact |
| **Socket 1A Mode** | `ON` / `TCPS` (TCP Server) | Listens for incoming TCP connections |
| **Socket 1A Local Port** | `8010` | Supports up to 8 concurrent TCP clients |

---

### 3. Quick Start (CLI & Netcat)

#### Using `tk700.py` (Zero Dependencies)

```bash
# Optional: override default serial server address/port (default: 192.168.5.40:8010)
export BENQ_HOST="192.168.5.40"
export BENQ_PORT="8010"

# Full status check (Model, Power, Source, Picture Mode, Lamp Mode & Hours, etc.)
python3 tk700.py status

# Power ON / OFF
python3 tk700.py on
python3 tk700.py off

# Switch HDMI inputs
python3 tk700.py hdmi1
python3 tk700.py hdmi2
python3 tk700.py hdmi3

# Switch Picture Modes & Lamp Power Modes
python3 tk700.py mode-hdr
python3 tk700.py mode-game
python3 tk700.py mode-cinema
python3 tk700.py lamp-eco
python3 tk700.py lamp-normal

# Send any raw BenQ RS232 command
python3 tk700.py "ltim=?"
```

#### One-Liners with `nc` (Netcat)

```bash
printf "\r*pow=?#\r"     | nc -w 1 192.168.5.40 8010   # Query power
printf "\r*pow=on#\r"    | nc -w 1 192.168.5.40 8010   # Power ON
printf "\r*pow=off#\r"   | nc -w 1 192.168.5.40 8010   # Power OFF
printf "\r*sour=hdmi#\r" | nc -w 1 192.168.5.40 8010   # Switch to HDMI 1
printf "\r*sour=hdmi2#\r"| nc -w 1 192.168.5.40 8010   # Switch to HDMI 2
```

---

### 4. Home Assistant Configuration

#### Option A: HACS `BenQ Projector` Integration (Recommended)

1. **Install via HACS**: Go to **HACS -> Integrations**, search for **`BenQ Projector`** (`rrooggiieerr/homeassistant-benqprojector`), download it, and restart Home Assistant.
2. **Add Integration**: Go to **Settings -> Devices & Services -> Add Integration -> `BenQ Projector`**.
3. **Connection Setup**:
   - **Type**: **Network / Serial over IP**
   - **Host**: `192.168.5.40`
   - **Port**: `8010`
   - **Baudrate**: `115200`
4. **Entities Created**:
   - Primary entity: `media_player.benq_tk700` (`device_class: tv`, power, HDMI input source selection, volume/mute).
   - Additional entities: Lamp hours (`sensor.*_lamp_time`), Picture Mode (`select.*_picture_mode`), Lamp Mode (`select.*_lamp_mode`), Blank screen (`switch.*_blank`), etc.

#### Option B: Native `configuration.yaml` (No HACS Required)

See the [`command_line` and `shell_command` YAML snippet above](#方式-b原生-configurationyaml-免插件配置) to expose switches, sensors, and shell actions directly in `configuration.yaml`.

---

### 5. Apple HomeKit Integration (TV Accessory Mode)

To expose the projector to Apple HomeKit as a native **TV Accessory** (enabling power toggle, HDMI input switching in the Home app, iOS Control Center remote, and Siri commands):

#### Option A: Via Home Assistant UI

1. Ensure `media_player.benq_tk700` has its device class ("Show as") set to **`tv`**.
2. Go to **Settings -> Devices & Services -> Add Integration -> `HomeKit Bridge`**.
3. Configure the instance:
   - **Domains to include**: Select **`Media Player`**.
   - **HomeKit Mode**: Select **`accessory`** (Apple HomeKit requires Television `media_player` entities to run in standalone `accessory` mode rather than `bridge` mode).
   - **Entity**: Select **`media_player.benq_tk700`**.
4. Open **Notifications** in Home Assistant and scan the generated QR pairing code in the iOS **Home** app (`+` -> **Add Accessory**).

#### Option B: Via `configuration.yaml`

```yaml
homeassistant:
  customize:
    media_player.benq_tk700:
      device_class: tv
      friendly_name: "BenQ TK700"

homekit:
  - name: "HomeKit-BenQ-TK700"
    port: 21065
    mode: accessory
    filter:
      include_entities:
        - media_player.benq_tk700
```

#### Hardware State Machine Notes (Warm-up & Cool-down)

- **Warm-up (~40s after power on)**: While the lamp is warming up, `pow=off` commands are ignored by the projector (`*Block item#`). Wait until the video source appears before sending power-off or input-switch commands.
- **Cool-down (~90s after power off)**: While cooling fans are running after power-off, serial queries return `*Block item#`. Home Assistant temporarily marks the entity `unavailable` (and HomeKit shows `No Response`) until cooling finishes and the state settles to `off`.

---

## 📄 Detailed Protocol Reference

See [`RS232.md`](./RS232.md) for the complete UETEL UE-E5410 HTTP CGI API documentation and the full BenQ TK700 RS232 command reference table.
