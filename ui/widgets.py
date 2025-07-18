# ui/widgets.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

class MatplotlibCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax_tekengebied = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)

class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.load_button = QPushButton('Laad DXF')
        self.export_order_button = QPushButton('Exporteer Bestellijst')
        self.export_flowering_button = QPushButton('Exporteer Bloeikalender')
        self.export_image_button = QPushButton('Exporteer Afbeeldingenlayout')
        
        self.species_label = QLabel('Plantsoort:'); self.species_input = QLineEdit()
        self.density_label = QLabel('Planten per m²:'); self.density_input = QLineEdit()
        self.area_label = QLabel('Oppervlakte: -- m²'); self.plants_label = QLabel('Aantal planten: --')
        
        self.order_list_label = QLabel('Bestellijst:'); self.order_list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.order_list_display = QTextEdit(); self.order_list_display.setReadOnly(True)
        
        widgets = [self.load_button, self.export_order_button, self.export_flowering_button, self.export_image_button,
                   self.species_label, self.species_input, self.density_label, self.density_input, 
                   self.area_label, self.plants_label, self.order_list_label, self.order_list_display]
        for w in widgets: layout.addWidget(w)
        self.setLayout(layout)