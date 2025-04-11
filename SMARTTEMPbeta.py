#VER:1.2.2
#THIS DOES NOT WORK
#If it does, I need to buy a lottery ticket
import sys
import time
import os
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

    if elapsed <= 0:  # Safety check to avoid division by zero
        return 0, 0

    read_speed = (current.read_bytes - prev.read_bytes) / elapsed / 1024  # KB/s
    write_speed = (current.write_bytes - prev.read_bytes) / elapsed / 1024  # KB/s

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

class ClockView(QWidget):
    def __init__(self):
        super().__init__()
        self.prev_net = psutil.net_io_counters()
        self.prev_net_time = time.time()
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
        self.prev_net = psutil.net_io_counters()
        self.prev_net_time = time.time()
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S\n%A, %B %d"))

screen_index = 1 

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.prev_net = psutil.net_io_counters()
        self.prev_net_time = time.time()
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
        self.status_label = QLabel("Initalizing...")
        self.status_label.setFixedHeight(60)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.status_label.setStyleSheet(self.make_status_style("NA"))
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
        elif status == "!!":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #ff0000);"
        elif status == "NA":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 gray, stop:1 black);"
        elif status == "note":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0000ff, stop:1 black);"
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
        
        # Process Box
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Memory %"])
        self.table.setSortingEnabled(True)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.update_processes()
        

		# Network Box
        self.network_box, self.network_layout = create_component_box("Network")
        self.network_label = QLabel("Loading network data...")
        self.network_label.setStyleSheet("color: white; font-size: 18px;")
        self.network_layout.addWidget(self.network_label)
        
        layout.addWidget(self.network_box)

    def update_network_info(self):
        # Initialize the previous network state and time if it's the first call
            if not hasattr(self, 'prev_net') or not hasattr(self, 'prev_net_time'):
                self.prev_net = psutil.net_io_counters()  # Initialize network stats
                self.prev_net_time = time.time()  # Initialize time

            current = psutil.net_io_counters()
            current_time = time.time()

            elapsed = current_time - self.prev_net_time
            if elapsed <= 0:
                return  # Avoid division by zero or negative time difference

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

            # Update the label with the calculated speeds
            self.network_label.setText(
                f"Download: {format_speed(download_speed)}\nUpload: {format_speed(upload_speed)}"
            )


	def update_processes(self):
		self.table.setRowCount(0)
    	for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        	row_position = self.table.rowCount()
        	self.table.insertRow(row_position)
        	self.table.setItem(row_position, 0, QTableWidgetItem(str(proc.info['pid'])))
        	self.table.setItem(row_position, 1, QTableWidgetItem(proc.info['name']))
        	self.table.setItem(row_position, 2, QTableWidgetItem(f"{proc.info['cpu_percent']:.1f}"))
        	self.table.setItem(row_position, 3, QTableWidgetItem(f"{proc.info['memory_percent']:.1f}"))

    def update_stats(self):
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.setText(f"Intel 14900k 12th Gen i9\n"
                               f"CPU Usage: {cpu_percent}%/s"
                               )

        gpus = GPUtil.getGPUs()
        gpu = gpus[0]
        gpu_temp = gpu.temperature
        gpu_percent = gpu.memoryUtil * 100
        gpu_percent = gpus[0].memoryUtil * 100 if gpus else 0  # Assuming 1 GPU; adjust for multi-GPU systems
        self.gpu_temp_label.setText(f"PNY 4060ti 16GB\n"
                                    f"Temp: {gpu_temp}°C\n"
                                    f"Usage: {gpu_percent:.1f}%/s"
                                    )
        
        # RAM Usage
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        used_gb = memory.used / (1024 ** 3)
        rm_percent = memory.percent
        self.ram_label.setText(f"Corsair Vengence RGB DDR5 16GB (2x)\n"
                               f"RAM: {used_gb:.1f} GB / {total_gb:.1f} GB\n"
                               f"Usage: {rm_percent}%/s"
                               )

		# Storage Usage
        # Inside update_stats()
        drives = psutil.disk_partitions()
        storage_info = []

        labels = get_drive_labels()
        storage_info = []

        def is_removable(path):
            try:
                drive_type = win32file.GetDriveType(path)
                return drive_type == win32file.DRIVE_REMOVABLE
            except Exception:
                return False
        for drive in drives:
            if 'cdrom' in drive.opts == '':
                continue

        for drive in drives:
            if 'cdrom' in drive.opts or not os.path.exists(drive.device):
                continue  # Skip CD-ROM or inaccessible drives

            usage = psutil.disk_usage(drive.mountpoint)
            label = "USB" if is_removable(drive.device) else "Drive"
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            percent = usage.percent
            read_kb, write_kb = get_disk_io_speed()
            label1 = labels.get(drive.device, "Unknown")

            storage_info.append(
                f"{label}: ({drive.device}) {label1}\n"
                f"  Used: {used_gb:.1f} / {total_gb:.1f} GB ({percent}%)\n"
                f"  Read: {read_kb:.0f} KB/s | Write: {write_kb:.0f} KB/s"
            )

        self.storage_label.setText("\n\n".join(storage_info))


        self.update_network_info()

		self.process_monitor = ProcessMonitor()
		self.tabs.addTab(self.process_monitor, "Processes")
        self.timer.timeout.connect(self.process_monitor.update_processes)
		self.timer.start(5000)


        # Update top bar based on CPU usage
        if cpu_percent > 98:
            self.status_label.setText("ALERT: MAX CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif gpu_temp > 90:
            self.status_label.setText(f"ALERT: GPU {gpu_temp}°C")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif gpu_percent > 98:
            self.status_label.setText("ALERT: MAX GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif rm_percent > 98:
            self.status_label.setText("ALERT: MAX RAM USAGE")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif cpu_percent > 90:
            self.status_label.setText(f"WARNING: {cpu_percent}% CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("alert"))
        elif gpu_percent > 90:
            self.status_label.setText(f"WARNING: {gpu_percent}% GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("alert"))
        elif gpu_temp > 80:
            self.status_label.setText(f"WARNING: GPU {gpu_temp}°C")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif rm_percent > 90:
            self.status_label.setText(f"WARNING: {percent}% RAM USAGE")
            self.status_label.setStyleSheet(self.make_status_style("alert"))
        elif cpu_percent > 70:
            self.status_label.setText(f"CAUTION: {cpu_percent}% CPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif gpu_percent > 70:
            self.status_label.setText(f"CAUTION: {gpu_percent}% GPU USAGE")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif gpu_temp > 65:
            self.status_label.setText(f"CAUTION: GPU {gpu_temp}°C")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif rm_percent > 70:
            self.status_label.setText(f"CAUTION: {percent}% RAM USAGE")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif percent > 98:
            self.status_label.setText(f"{label1} IS FULL")
            self.status_label.setStyleSheet(self.make_status_style("critical"))
        elif percent > 90:
            self.status_label.setText(f"CAUTION: {label1} IS {percent}% FULL")
            self.status_label.setStyleSheet(self.make_status_style("warning"))
        elif label == "USB":
            self.status_label.setText(f"NOTICE: USB INSERTED ({label1})")
            self.status_label.setStyleSheet(self.make_status_style("note"))
        else:
            self.status_label.setText("System: OK")
            self.status_label.setStyleSheet(self.make_status_style("normal"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())
