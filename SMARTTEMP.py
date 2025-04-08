import sys
import time
import ctypes
import string
import win32file
import psutil
import GPUtil
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox, QStackedLayout
)
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

def create_component_box(title):
    box = QGroupBox(title)
    box.setStyleSheet("""
        QGroupBox {
            border: 2px solid white;
            border-radius: 10px;
            margin-top: 20px;
            color: white;
            font-weight: bold;
            font-size: 25px;
        }
                      QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; /* Keep the title at the top center */
            padding-top: 7px;  /* Adjust this value to move the title up */
            padding-left: 0px;
            padding-right: 10px;
        }
    """)
    box.setFont(QFont("Segoe UI", 12))
    layout = QVBoxLayout()
    box.setLayout(layout)
    return box, layout

def get_gpu_info():
    gpus = GPUtil.getGPUs()
    gpu_info = []
    
    for gpu in gpus:
        gpu_name = gpu.name
        gpu_temp = gpu.temperature  # Temperature of the GPU
        gpu_percent = gpu.memoryUtil * 100  # Memory usage percentage
        gpu_info.append((gpu_name, gpu_temp, gpu_percent))
    
    return gpu_info


# Call this once during initialization
prev = psutil.disk_io_counters()
prev_time = time.time()

def get_disk_io_speed():
    global prev, prev_time

    current = psutil.disk_io_counters()
    current_time = time.time()
    elapsed = current_time - prev_time

    read_speed = (current.read_bytes - prev.read_bytes) / elapsed / 1024  # KB/s
    write_speed = (current.write_bytes - prev.write_bytes) / elapsed / 1024  # KB/s

    prev = current
    prev_time = current_time

    return read_speed, write_speed
    
def get_drive_labels():
    labels = {}
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    
    for drive in drives:
        label_buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            label_buf,
            ctypes.sizeof(label_buf),
            None,
            None,
            None,
            None,
            0
        )
        labels[drive] = label_buf.value if label_buf.value else "Local Disk"
    return labels
    
    labels = get_drive_labels()

for drive in psutil.disk_partitions():
    if 'cdrom' in drive.opts or drive.fstype == '':
        continue
    usage = psutil.disk_usage(drive.mountpoint)
    label = labels.get(drive.device, "Unknown")
    print(f"{label} ({drive.device}) - {usage.used / 1e+9:.1f} GB / {usage.total / 1e+9:.1f} GB")

def is_removable(path):
    try:
        drive_type = win32file.GetDriveType(path)
        return drive_type == win32file.DRIVE_REMOVABLE
    except Exception:
        return False
for drive in drives:
    if 'cdrom' in drive.opts or drive.fstype == '':
        continue

    usage = psutil.disk_usage(drive.mountpoint)
    label = "USB" if is_removable(drive.device) else "Drive"
    storage_info.append(f"{label} {drive.device} {used:.1f} / {total:.1f} GB ({percent}%)")

def update_network_info(self):
    current = psutil.net_io_counters()
    current_time = time.time()

    elapsed = current_time - self.prev_net_time
    if elapsed == 0:
        return  # Avoid divide by zero

    download_speed = (current.bytes_recv - self.prev_net.bytes_recv) / elapsed
    upload_speed = (current.bytes_sent - self.prev_net.bytes_sent) / elapsed

    self.prev_net = current
    self.prev_net_time = current_time

    # Convert to readable format
    def format_speed(bps):
        if bps > 1024**2:
            return f"{bps / 1024**2:.2f} MB/s"
        elif bps > 1024:
            return f"{bps / 1024:.1f} KB/s"
        else:
            return f"{bps:.0f} B/s"

    self.network_label.setText(
        f"Download: {format_speed(download_speed)}\nUpload: {format_speed(upload_speed)}"
    )

class ClockView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.clock_label.setStyleSheet("color: white; font-size: 72px; font: Arial;")
        layout.addWidget(self.clock_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S\n%A, %B %d"))

screen_index = 1 

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(0, 0, 1920, 515)
        self.setStyleSheet("background-color: black;")
        screens = QGuiApplication.screens()
        if screen_index < len(screens):
            screen = screens[screen_index]
            geometry = screen.geometry()
            self.setGeometry(geometry)  # Position + size
        else:
            print("Monitor index out of range. Defaulting to primary.")
        self.showFullScreen()

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.main_layout.setSpacing(0)  # Remove spacing between items
        self.setLayout(self.main_layout)

        # Top Status Bar
        self.status_label = QLabel("System OK")
        self.status_label.setFixedHeight(60)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.status_label.setStyleSheet(self.make_status_style("normal"))
        self.main_layout.addWidget(self.status_label)

        # Stacked views
        self.stack = QStackedLayout()
        self.main_layout.addLayout(self.stack)

        # Views
        self.monitor_view = QWidget()
        self.build_monitor_view()
        self.clock_view = ClockView()

        self.stack.addWidget(self.monitor_view)
        self.stack.addWidget(self.clock_view)

        # Nav buttons
        nav_layout = QHBoxLayout()
        self.btn_monitor = QPushButton("Tempatures")
        self.btn_clock = QPushButton("Clock")
        for btn in [self.btn_monitor, self.btn_clock]:
            btn.setStyleSheet("background-color: #333; color: white; font-size: 16px;")
            btn.setFixedHeight(40)
            nav_layout.addWidget(btn)

        self.main_layout.addLayout(nav_layout)

        self.btn_monitor.clicked.connect(lambda: self.stack.setCurrentWidget(self.monitor_view))
        self.btn_clock.clicked.connect(lambda: self.stack.setCurrentWidget(self.clock_view))

        # Update Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.update_stats()

    def make_status_style(self, status):
        if status == "normal":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ff00, stop:1 black);"
        elif status == "warning":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fcec03, stop:1 black);"
        elif status == "alert":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fc6b03, stop:1 black);"
        elif status == "critical":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff0000, stop:1 black);"
        elif status == "NA":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 gray, stop:1 black);"
        else:
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 black, stop:1 black);"

        return f"""
            background: {gradient}
            color: white;
            padding: 10px;
        """

    def build_monitor_view(self):
        layout = QHBoxLayout()
        self.monitor_view.setLayout(layout)

        # CPU Box
        self.cpu_box, self.cpu_layout = create_component_box("CPU")
        self.cpu_usage = QLabel()
        self.cpu_usage.setStyleSheet("color: white; font-size: 18px;")
        self.cpu_layout.addWidget(self.cpu_usage)

        layout.addWidget(self.cpu_box)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # GPU Box
        self.gpu_box, self.gpu_layout = create_component_box("GPU")
        self.gpu_temp_label = QLabel()
		self.gpu_temp_label.setStyleSheet("color: white; font-size: 18px;")
		self.gpu_layout.addWidget(self.gpu_temp_label)
        self.gpu_usage = QLabel()
        self.gpu_usage.setStyleSheet("color: white; font-size: 18px;")
        self.gpu_layout.addWidget(self.gpu_usage)

        layout.addWidget(self.gpu_box)
        
        # RAM Box
		self.ram_box, self.ram_layout = create_component_box("RAM")
		self.ram_label = QLabel()
		self.ram_label.setStyleSheet("color: white; font-size: 18px;")
		self.ram_layout.addWidget(self.ram_label)
        
		layout.addWidget(self.ram_box)
        
        # Storage Box
		self.storage_box, self.storage_layout = create_component_box("Storage")
		self.storage_label = QLabel()
		self.storage_label.setStyleSheet("color: white; font-size: 18px;")
		self.storage_layout.addWidget(self.storage_label)

		layout.addWidget(self.storage_box)

		# Network Box
		self.network_box, self.network_layout = create_component_box("Network")
		self.network_label = QLabel("Loading network data...")
		self.network_label.setStyleSheet("color: white; font-size: 18px;")
		self.network_layout.addWidget(self.network_label)
        
		layout.addWidget(self.network_box)

    def update_stats(self):
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.setText(f"Intel 14900k 12th Gen i9 | CPU Usage: {cpu_percent}%")

        gpus = GPUtil.getGPUs()
        gpu_temp = gpu.temperature
        gpu_percent = gpus[0].memoryUtil * 100 if gpus else 0  # Assuming 1 GPU; adjust for multi-GPU systems
        self.gpu_temp_label.setText(f"PNY 4060ti | Temp: {gpu_temp}°C | Usage: {gpu_usage:.1f}%")
        
        # RAM Usage
		memory = psutil.virtual_memory()
		total_gb = memory.total / (1024 ** 3)
		used_gb = memory.used / (1024 ** 3)
		percent = memory.percent
		self.ram_label.setText(f"Corsair Vengence RGB DDR5 16GB (2x) | RAM: {used_gb:.1f} GB / {total_gb:.1f} GB | Usage: {percent}%")

		# Storage Usage
		drives = psutil.disk_partitions()
		storage_info = []

		for drive in drives:
  		  if 'cdrom' in drive.opts == '':
    	    continue  # Skip empty or CD-ROM drives

    	usage = psutil.disk_usage(drive.mountpoint)
    	total_gb = usage.total / (1024 ** 3)
    	used_gb = usage.used / (1024 ** 3)
    	percent = usage.percent
		read_kb, write_kb = get_disk_io_speed()
		self.storage_label.setText(
    		f"{label} ({drive.device})\n"
    		f"Used: {used_gb:.1f} / {total_gb:.1f} GB ({percent}%)\n"
    		f"Read: {read_kb:.0f} KB/s | Write: {write_kb:.0f} KB/s"
		)

		self.storage_label.setText("\n".join(storage_info))

		self.update_network_info()

        # Update top bar based on CPU usage
        if cpu_percent > 98:
            self.status_label.setText("ALERT: MAX CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif gpu_percent > 98:
            self.status_label.setText("ALERT: MAX GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif cpu_percent > 90:
            self.status_label.setText("WARNING: >90% CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("alert"))
        elif gpu_percent > 90:
            self.status_label.setText("WARNING: >90% GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("alert"))
        elif cpu_percent > 70:
            self.status_label.setText("CAUTION: >70% CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif gpu_percent > 70:
            self.status_label.setText("CAUTION: >70% GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        else:
            self.status_label.setText("System: OK")
            self.status_label.setStyleSheet(self.make_status_style("normal"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())
