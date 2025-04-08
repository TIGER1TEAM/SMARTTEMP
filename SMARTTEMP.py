import sys
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
import sys

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
		self.ram_label.setText(f"RAM: {used_gb:.1f} GB / {total_gb:.1f} GB ({percent}%)")

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
