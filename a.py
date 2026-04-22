import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading
import csv
import time
import dataclasses
import json
import os
from pathlib import Path
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

MAX_RECORDS = 1200
POLL_INTERVAL_MS = 100
PLOT_UPDATE_INTERVAL_MS = 250
MAX_QUEUE_ITEMS_PER_POLL = 200

# ============================================================
# 1. 資料結構定義
# ============================================================

@dataclasses.dataclass
class SystemStats:
    """統計通訊與解析狀態"""
    rx_lines: int = 0
    non_tel_lines: int = 0
    valid_packets: int = 0
    checksum_fail: int = 0
    parse_fail: int = 0

@dataclasses.dataclass
class UnifiedTelemetryRecord:
    """統一遙測資料格式 - 對應 STM32 $TEL 欄位"""
    timestamp: str  # 時間戳
    mcu_tick_ms: int
    gps_date: str
    gps_time: str
    rtc_date: str
    rtc_time: str
    gps_valid: int
    fix_quality: int
    satellites: int
    hdop: float
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    speed_knots: float
    speed_kmh: float
    course_deg: float
    
    def to_csv_row(self):
        """轉換為 CSV 行"""
        return [
            self.timestamp, self.mcu_tick_ms,
            self.gps_date, self.gps_time, self.rtc_date, self.rtc_time,
            self.gps_valid, self.fix_quality, self.satellites,
            self.hdop, self.latitude_deg, self.longitude_deg,
            self.altitude_m, self.speed_knots, self.speed_kmh, self.course_deg
        ]

class TelParser:
    """解析 $TEL 格式的遙測數據包"""
    
    @staticmethod
    def parse_line(line: str) -> UnifiedTelemetryRecord:
        """
        解析 $TEL 封包並驗證 Checksum
        格式: $TEL,tick,gps_date,gps_time,rtc_date,rtc_time,gps_valid,
             fix_quality,satellites,hdop,lat,lon,alt,speed_knots,speed_kmh,course*CS\r\n
        """
        line = line.strip()

        # 某些情況下串流前面可能夾帶雜訊字元，嘗試從 $TEL 起點恢復
        tel_pos = line.find("$TEL,")
        if tel_pos > 0:
            line = line[tel_pos:]
        
        # 檢查 Header
        if not line.startswith("$TEL,"):
            raise ValueError("Invalid Header: must start with $TEL")
        
        # 檢查 Checksum
        if "*" not in line:
            raise ValueError("No Checksum found")
        
        # 分離 Payload 和 Checksum
        payload, expected_cs = line[1:].split("*", 1)  # 移除 $ 符號
        
        # 計算 Checksum (XOR)
        calc_cs = 0
        for char in payload:
            calc_cs ^= ord(char)
        
        if f"{calc_cs:02X}".upper() != expected_cs.upper():
            raise ValueError(f"Checksum Mismatch: calc={calc_cs:02X}, expected={expected_cs}")
        
        # 解析欄位
        fields = payload.split(",")
        
        if len(fields) < 16:  # 包含 TEL 標籤 + 15 個資料欄位
            raise ValueError(f"Not enough fields: got {len(fields)}, expected 16")
        
        try:
            record = UnifiedTelemetryRecord(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                mcu_tick_ms=int(fields[1]),
                gps_date=fields[2],
                gps_time=fields[3],
                rtc_date=fields[4],
                rtc_time=fields[5],
                gps_valid=int(fields[6]),
                fix_quality=int(fields[7]),
                satellites=int(fields[8]),
                hdop=float(fields[9]),
                latitude_deg=float(fields[10]),
                longitude_deg=float(fields[11]),
                altitude_m=float(fields[12]),
                speed_knots=float(fields[13]),
                speed_kmh=float(fields[14]),
                course_deg=float(fields[15])
            )
            return record
        except (ValueError, IndexError) as e:
            raise ValueError(f"Field parsing error: {e}")

class SerialWorker(threading.Thread):
    """背景串口讀取線程"""
    
    def __init__(self, port: str, baud: int, data_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.data_queue = data_queue
        self.stop_event = stop_event
        self.ser = None
        
    def run(self):
        """執行串口讀取迴圈"""
        if not SERIAL_AVAILABLE:
            self.data_queue.put(("error", "pyserial not installed"))
            return
            
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.data_queue.put(("status", f"Connected to {self.port} @ {self.baud} baud"))
            
            while not self.stop_event.is_set():
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore')
                        if line:
                            self.data_queue.put(("line", line))
                except Exception as e:
                    self.data_queue.put(("error", f"Read error: {e}"))
                    
        except serial.SerialException as e:
            self.data_queue.put(("error", f"Serial Error: {e}"))
        finally:
            if self.ser:
                self.ser.close()
    
    def close_port(self):
        """關閉串口"""
        if self.ser:
            self.ser.close()

class CSVLogger:
    """CSV 數據記錄器"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd() / "GPS_Records"
        self.base_path.mkdir(exist_ok=True)
        
        # 創建日期子目錄
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_dir = self.base_path / today
        self.log_dir.mkdir(exist_ok=True)
        
        # 初始化 CSV 檔案
        self.csv_file = self.log_dir / f"GPS_Record_{today}.csv"
        self._write_header()
        
    def _write_header(self):
        """寫入 CSV 標題列"""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'MCU_Tick_ms',
                    'GPS_Date', 'GPS_Time', 'RTC_Date', 'RTC_Time',
                    'GPS_Valid', 'Fix_Quality', 'Satellites', 'HDOP',
                    'Latitude', 'Longitude', 'Altitude_m', 'Speed_knots',
                    'Speed_kmh', 'Course_deg'
                ])
    
    def write(self, record: UnifiedTelemetryRecord):
        """寫入記錄到 CSV"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(record.to_csv_row())
        except Exception as e:
            print(f"CSV write error: {e}")
    
    def close(self):
        """關閉記錄器"""
        pass

# ============================================================
# 2. 主程式 GUI 類別
# ============================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GPS Telemetry Dashboard")
        self.geometry("1400x900")
        
        # 初始化核心數據
        self.q = queue.Queue()
        self.stats = SystemStats()
        self.records = []
        self.stop_event = threading.Event()
        self.auto_save = False
        self.auto_map = False
        self.last_plot_update_ts = 0.0
        
        # 配置文件讀取
        self.config = self._load_config()
        self.csv_logger = None
        self.serial_worker = None
        
        # UI 變數
        self.status_text = tk.StringVar(value="Waiting for data...")
        
        # 初始化 UI
        self._setup_ui()
        self._setup_plots()
        
        # 啟動輪詢
        self.after(POLL_INTERVAL_MS, self.poll_queue)
        
        # 視窗關閉協定
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _load_config(self):
        """從 JSON 配置文件讀取設定"""
        config_file = Path.cwd() / "dht11_gui_config.json"
        default_config = {
            "port": "COM3",
            "baud": 115200,
            "save_base_path": str(Path.cwd() / "GPS_Records")
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return default_config
    
    def _setup_ui(self):
        """建立使用者介面"""
        # 上方控制面板
        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 串口設定
        ttk.Label(control_frame, text="Port:").pack(side=tk.LEFT, padx=2)
        self.port_var = tk.StringVar(value=self.config.get("port", "COM3"))
        port_combo = ttk.Combobox(control_frame, textvariable=self.port_var, width=8, 
                                   values=["COM1", "COM2", "COM3", "COM4", "COM5"])
        port_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(control_frame, text="Baud:").pack(side=tk.LEFT, padx=2)
        self.baud_var = tk.StringVar(value=str(self.config.get("baud", 115200)))
        baud_combo = ttk.Combobox(control_frame, textvariable=self.baud_var, width=8,
                                   values=["9600", "115200", "230400"])
        baud_combo.pack(side=tk.LEFT, padx=2)
        
        # 控制按鈕
        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.connect_serial)
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.disconnect_btn = ttk.Button(control_frame, text="Disconnect", command=self.disconnect_serial, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)

        self.clear_btn = ttk.Button(control_frame, text="Clear Data", command=self.clear_data)
        self.clear_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 記錄選項
        self.auto_save_var = tk.BooleanVar(value=False)
        auto_save_check = ttk.Checkbutton(control_frame, text="Auto CSV Save", variable=self.auto_save_var, command=self._toggle_csv_save)
        auto_save_check.pack(side=tk.LEFT, padx=2)
        
        self.auto_map_var = tk.BooleanVar(value=False)
        auto_map_check = ttk.Checkbutton(control_frame, text="Auto Map Refresh", variable=self.auto_map_var)
        auto_map_check.pack(side=tk.LEFT, padx=2)
        
        # 統計信息
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.stat_label = tk.StringVar(value="RX:0 | TEL:0 | Valid:0 | CRC Fail:0 | Parse Fail:0")
        stat_display = ttk.Label(control_frame, textvariable=self.stat_label)
        stat_display.pack(side=tk.LEFT, padx=5)
        
        # 中間：圖表區域
        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 狀態欄
        status_bar = ttk.Label(self, textvariable=self.status_text, relief=tk.SUNKEN, anchor='w')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)
        
        # 終端機輸出
        terminal_label = ttk.Label(self, text="Debug Terminal:")
        terminal_label.pack(side=tk.TOP, anchor='w', padx=5)
        
        self.terminal = tk.Text(self, height=6, bg="#1e1e1e", fg="#d4d4d4", font=("Courier", 9))
        self.terminal.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 將圖表放入 plot_frame
        self.plot_frame = plot_frame
    
    def _setup_plots(self):
        """初始化 Matplotlib 圖表"""
        self.fig = Figure(figsize=(12, 5), dpi=100)
        
        # 2D 軌跡圖 (佔左側 2/3)
        self.ax_track = self.fig.add_subplot(131)
        self.ax_track.set_title("2D Trajectory (Latitude / Longitude)")
        self.ax_track.set_xlabel("Longitude")
        self.ax_track.set_ylabel("Latitude")
        self.ax_track.grid(True)
        
        # 速度時間序列 (右上)
        self.ax_speed = self.fig.add_subplot(232)
        self.ax_speed.set_title("Speed (km/h)")
        self.ax_speed.set_xlabel("Sample #")
        self.ax_speed.set_ylabel("Speed")
        self.ax_speed.grid(True)
        
        # 衛星數 / HDOP (右中)
        self.ax_sat = self.fig.add_subplot(233)
        self.ax_sat.set_title("Satellites & HDOP")
        self.ax_sat.set_xlabel("Sample #")
        self.ax_sat.set_ylabel("Count / Value")
        self.ax_sat.grid(True)
        self.ax_sat_hdop = self.ax_sat.twinx()
        
        # 高度時間序列 (右下)
        self.ax_alt = self.fig.add_subplot(235)
        self.ax_alt.set_title("Altitude (m)")
        self.ax_alt.set_xlabel("Sample #")
        self.ax_alt.set_ylabel("Altitude")
        self.ax_alt.grid(True)
        
        # 信號質量 (右下右)
        self.ax_quality = self.fig.add_subplot(236)
        self.ax_quality.set_title("Fix Quality")
        self.ax_quality.set_xlabel("Sample #")
        self.ax_quality.set_ylabel("Quality")
        self.ax_quality.grid(True)
        
        self.fig.tight_layout()
        
        # 內嵌到 Tk
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def connect_serial(self):
        """連接到串口"""
        try:
            port = self.port_var.get()
            baud = int(self.baud_var.get())
            
            if not SERIAL_AVAILABLE:
                messagebox.showerror("Error", "pyserial module not installed")
                return
            
            self.serial_worker = SerialWorker(port, baud, self.q, self.stop_event)
            self.serial_worker.start()
            
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_text.set(f"Connecting to {port}...")
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect_serial(self):
        """斷開串口連接"""
        try:
            if self.serial_worker:
                self.serial_worker.close_port()
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.status_text.set("Disconnected")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _toggle_csv_save(self):
        """切換 CSV 記錄狀態"""
        if self.auto_save_var.get():
            try:
                self.csv_logger = CSVLogger(self.config.get("save_base_path"))
                self.append_terminal(f"CSV logging started: {self.csv_logger.csv_file}")
            except Exception as e:
                messagebox.showerror("CSV Error", str(e))
                self.auto_save_var.set(False)
        else:
            if self.csv_logger:
                self.csv_logger.close()
                self.append_terminal("CSV logging stopped")
                self.csv_logger = None
    
    def append_terminal(self, message: str):
        """添加消息到終端機"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"[{timestamp}] {message}\n")
        self.terminal.see(tk.END)

    def clear_data(self):
        """清除累積資料，降低重繪負擔"""
        self.records.clear()
        self.stats = SystemStats()
        self._update_stats()
        self.status_text.set("Data cleared")
        self._redraw_all(force_clear=True)
        self.append_terminal("[INFO] Data cleared")
    
    def poll_queue(self):
        """輪詢數據隊列"""
        parsed_new_record = False
        processed = 0
        try:
            while processed < MAX_QUEUE_ITEMS_PER_POLL:
                kind, payload = self.q.get_nowait()
                processed += 1
                
                if kind == "line":
                    self.stats.rx_lines += 1
                    line = payload.strip()
                    if not line:
                        continue

                    # STM32 的 USART1 可能同時輸出 [DBG]/[TEST] 與 $TEL。
                    # 非 $TEL 行不視為解析錯誤，避免污染 Parse Fail 統計。
                    if not line.startswith("$TEL,"):
                        self.stats.non_tel_lines += 1
                        self._update_stats()
                        continue
                    
                    try:
                        rec = TelParser.parse_line(line)
                        self.records.append(rec)
                        if len(self.records) > MAX_RECORDS:
                            # 只保留最近 N 筆，避免長時間運行導致重繪越來越慢
                            self.records = self.records[-MAX_RECORDS:]
                        self.stats.valid_packets += 1
                        parsed_new_record = True
                        
                        # CSV 記錄
                        if self.auto_save_var.get() and self.csv_logger:
                            self.csv_logger.write(rec)
                        
                        # 更新狀態
                        self._update_stats()
                        self.status_text.set(
                            f"Valid: {self.stats.valid_packets} | "
                            f"Lat: {rec.latitude_deg:.4f} | "
                            f"Lon: {rec.longitude_deg:.4f} | "
                            f"Speed: {rec.speed_kmh:.1f} km/h"
                        )
                        
                    except ValueError as e:
                        msg = str(e)
                        if "Checksum" in msg:
                            self.stats.checksum_fail += 1
                        else:
                            self.stats.parse_fail += 1
                        self._update_stats()
                        self.append_terminal(f"[PARSE ERROR] {msg}")
                
                elif kind == "error":
                    self.append_terminal(f"[ERROR] {payload}")
                    self.status_text.set(payload)
                
                elif kind == "status":
                    self.append_terminal(f"[INFO] {payload}")
                    self.status_text.set(payload)
                    
        except queue.Empty:
            pass

        now = time.monotonic()
        if parsed_new_record and (now - self.last_plot_update_ts) * 1000.0 >= PLOT_UPDATE_INTERVAL_MS:
            self._redraw_all()
            self.last_plot_update_ts = now
        
        self.after(POLL_INTERVAL_MS, self.poll_queue)
    
    def _update_stats(self):
        """更新統計信息標籤"""
        tel_lines = self.stats.rx_lines - self.stats.non_tel_lines
        self.stat_label.set(
            f"RX:{self.stats.rx_lines} | "
            f"TEL:{tel_lines} | "
            f"Valid:{self.stats.valid_packets} | "
            f"CRC Fail:{self.stats.checksum_fail} | "
            f"Parse Fail:{self.stats.parse_fail}"
        )
    
    def _redraw_all(self, force_clear: bool = False):
        """重新繪製所有圖表"""
        if len(self.records) == 0:
            if force_clear:
                for ax in [self.ax_track, self.ax_speed, self.ax_sat, self.ax_alt, self.ax_quality]:
                    ax.clear()
                    ax.grid(True, alpha=0.3)
                self.ax_sat_hdop.clear()
                self.ax_track.set_title("2D Trajectory")
                self.ax_track.set_xlabel("Longitude")
                self.ax_track.set_ylabel("Latitude")
                self.ax_speed.set_title("Speed (km/h)")
                self.ax_speed.set_xlabel("Sample #")
                self.ax_speed.set_ylabel("Speed")
                self.ax_sat.set_title("Satellites & HDOP")
                self.ax_sat.set_xlabel("Sample #")
                self.ax_sat.set_ylabel("Count / Value")
                self.ax_sat_hdop.set_ylabel("HDOP")
                self.ax_alt.set_title("Altitude (m)")
                self.ax_alt.set_xlabel("Sample #")
                self.ax_alt.set_ylabel("Altitude")
                self.ax_quality.set_title("Fix Quality")
                self.ax_quality.set_xlabel("Sample #")
                self.ax_quality.set_ylabel("Quality")
                self.fig.tight_layout()
                self.canvas.draw_idle()
            return
        
        self._redraw_track()
        self._redraw_dashboard()
    
    def _redraw_track(self):
        """重新繪製 2D 軌跡"""
        self.ax_track.clear()
        self.ax_track.set_title("2D Trajectory")
        self.ax_track.set_xlabel("Longitude")
        self.ax_track.set_ylabel("Latitude")
        self.ax_track.grid(True)
        
        # 過濾有效的 GPS 座標
        valid_records = [r for r in self.records if r.gps_valid == 1]
        
        if valid_records:
            lons = [r.longitude_deg for r in valid_records]
            lats = [r.latitude_deg for r in valid_records]
            
            self.ax_track.plot(lons, lats, color='blue', linewidth=1, alpha=0.7)
            self.ax_track.scatter(lons[0], lats[0], marker='o', color='green', s=100, label='Start', zorder=5)
            self.ax_track.scatter(lons[-1], lats[-1], marker='x', color='red', s=100, label='End', zorder=5)
            self.ax_track.legend()
        
        self.canvas.draw_idle()
    
    def _redraw_dashboard(self):
        """重新繪製儀表板圖表"""
        if len(self.records) < 1:
            return
        
        # 清空所有子圖
        for ax in [self.ax_speed, self.ax_sat, self.ax_alt, self.ax_quality]:
            ax.clear()
        self.ax_sat_hdop.clear()
        
        # 準備數據
        sample_nums = list(range(len(self.records)))
        speeds = [r.speed_kmh for r in self.records]
        sats = [r.satellites for r in self.records]
        hdops = [r.hdop for r in self.records]
        alts = [r.altitude_m for r in self.records]
        qualities = [r.fix_quality for r in self.records]
        
        # 速度圖
        self.ax_speed.plot(sample_nums, speeds, color='blue', linewidth=1)
        self.ax_speed.fill_between(sample_nums, speeds, alpha=0.3, color='blue')
        self.ax_speed.set_title("Speed (km/h)")
        self.ax_speed.set_xlabel("Sample #")
        self.ax_speed.set_ylabel("Speed")
        self.ax_speed.grid(True, alpha=0.3)
        
        # 衛星 / HDOP 圖
        self.ax_sat.plot(sample_nums, sats, color='green', linewidth=2, label='Satellites')
        self.ax_sat_hdop.plot(sample_nums, hdops, color='orange', linewidth=1.5, label='HDOP', linestyle='--')
        self.ax_sat.set_title("Satellites & HDOP")
        self.ax_sat.set_xlabel("Sample #")
        self.ax_sat.set_ylabel("Satellites", color='green')
        self.ax_sat_hdop.set_ylabel("HDOP", color='orange')
        self.ax_sat.grid(True, alpha=0.3)
        self.ax_sat.legend(loc='upper left')
        
        # 高度圖
        self.ax_alt.plot(sample_nums, alts, color='purple', linewidth=1)
        self.ax_alt.fill_between(sample_nums, alts, alpha=0.3, color='purple')
        self.ax_alt.set_title("Altitude (m)")
        self.ax_alt.set_xlabel("Sample #")
        self.ax_alt.set_ylabel("Altitude")
        self.ax_alt.grid(True, alpha=0.3)
        
        # 信號質量圖
        self.ax_quality.bar(sample_nums, qualities, color='cyan', alpha=0.7)
        self.ax_quality.set_title("Fix Quality")
        self.ax_quality.set_xlabel("Sample #")
        self.ax_quality.set_ylabel("Quality")
        self.ax_quality.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw_idle()
    
    def on_close(self):
        """關閉程式時的安全清理"""
        try:
            self.stop_event.set()
            
            if self.serial_worker:
                self.serial_worker.close_port()
            
            if self.csv_logger:
                self.csv_logger.close()
            
            self.append_terminal("Application closing...")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.destroy()

# ============================================================
# 3. 執行進入點
# ============================================================

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()