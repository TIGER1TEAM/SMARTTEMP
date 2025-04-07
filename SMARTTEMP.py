from PyQt5.QtWidgets import QSpacerItem, QSizePolicy

class StatsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMARTTEMP")
        self.setGeometry(0, 0, 1920, 515)
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Status Bar
        self.status_label = QLabel("Initializing...")
        self.status_label.setFixedHeight(60)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(self.make_status_style("green"))
        self.status_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.main_layout.addWidget(self.status_label)

        # Component Boxes
        component_layout = QHBoxLayout()
        self.main_layout.addLayout(component_layout)

        # CPU Box
        self.cpu_box, self.cpu_layout = create_component_box("CPU")
        self.cpu_temp = QLabel()
        self.cpu_usage = QLabel()
        self.cpu_clock = QLabel()
        for label in (self.cpu_temp, self.cpu_usage, self.cpu_clock):
            label.setStyleSheet("color: white; font-size: 18px;")
            self.cpu_layout.addWidget(label)

        # GPU Box
        self.gpu_box, self.gpu_layout = create_component_box("GPU")
        self.gpu_temp = QLabel()
        self.gpu_usage = QLabel()
        self.gpu_clock = QLabel()
        for label in (self.gpu_temp, self.gpu_usage, self.gpu_clock):
            label.setStyleSheet("color: white; font-size: 18px;")
            self.gpu_layout.addWidget(label)

        # RAM Box
        self.ram_box, self.ram_layout = create_component_box("RAM")
        self.ram_usage = QLabel()
        self.ram_percent = QLabel()
        for label in (self.ram_usage, self.ram_percent):
            label.setStyleSheet("color: white; font-size: 18px;")
            self.ram_layout.addWidget(label)

        # Add all boxes
        component_layout.addWidget(self.cpu_box)
        component_layout.addWidget(self.gpu_box)
        component_layout.addWidget(self.ram_box)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.update_stats()

    def make_status_style(self, status):
        if status == "green":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ff00, stop:1 black);"
        elif status == "orange":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffff00, stop:1 black);"
        elif status == "red":
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff0000, stop:1 black);"
        else:
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 gray, stop:1 black);"

        return f"""
            background: {gradient}
            color: white;
            padding: 10px;
        """

    def update_stats(self):
        status = "green"
        message = "System OK"

        cpu_freq = psutil.cpu_freq()
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.setText(f"Usage: {cpu_percent}%")
        self.cpu_clock.setText(f"Clock: {cpu_freq.current:.0f} MHz")

        ram = psutil.virtual_memory()
        self.ram_usage.setText(f"Usage: {ram.used / (1024**3):.1f} / {ram.total / (1024**3):.1f} GB")
        self.ram_percent.setText(f"Percent: {ram.percent}%")

        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            gpu_temp = gpu.temperature
            self.gpu_temp.setText(f"Temp: {gpu_temp}°C")
            self.gpu_usage.setText(f"Usage: {gpu.load * 100:.0f}%")
            self.gpu_clock.setText(f"Clock: {gpu.clockSpeed} MHz")

            # Check GPU temp
            if gpu_temp > 85:
                status = "critical"
                message = "GPU Overheating!"
            elif gpu_temp > 70:
                status = "warning"
                message = "GPU Temperature High"

        self.status_label.setText(message)
        self.status_label.setStyleSheet(self.make_status_style(status))
