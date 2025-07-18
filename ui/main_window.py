# ui/main_window.py
import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QCompleter
from PyQt6.QtCore import Qt

from ui.widgets import MatplotlibCanvas, ControlPanel
from database.manager import DatabaseManager
from exporting.pdf_generator import generate_flowering_pdf, generate_order_list_pdf, generate_image_layout_pdf
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.patches import Polygon
import ezdxf
import numpy as np
from collections import defaultdict

def calculate_polygon_area(vertices):
    x = np.array([v[0] for v in vertices]); y = np.array([v[1] for v in vertices])
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def is_point_in_polygon(point, polygon_vertices):
    x, y = point; n = len(polygon_vertices); is_inside = False
    p1x, p1y = polygon_vertices[0]
    for i in range(n + 1):
        p2x, p2y = polygon_vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y: x_intersection = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= x_intersection: is_inside = not is_inside
        p1x, p1y = p2x, p2y
    return is_inside

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Plantencalculator Pro'); self.resize(1200, 700)
        self.db_manager = DatabaseManager('planten.db'); self.db_manager.connect()
        self.polygons_data = []; self.selected_poly_data = None
        self.species_color_map = {}; self.next_color_index = 0
        self.plant_names = self.db_manager.get_all_plant_names()
        self.COLOR_CYCLE = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f']
        self.initUI(); self.connect_signals(); self.setup_completer()

    def initUI(self):
        main_layout = QHBoxLayout()
        plot_container = QWidget(); plot_layout = QVBoxLayout()
        self.canvas = MatplotlibCanvas(self); toolbar = NavigationToolbar2QT(self.canvas, self)
        plot_layout.addWidget(toolbar); plot_layout.addWidget(self.canvas)
        plot_container.setLayout(plot_layout)
        self.controls = ControlPanel(); self.controls.setFixedWidth(350)
        main_layout.addWidget(plot_container); main_layout.addWidget(self.controls)
        self.setLayout(main_layout)

    def connect_signals(self):
        self.controls.load_button.clicked.connect(self.select_file)
        self.controls.export_order_button.clicked.connect(self.export_order_list_pdf)
        self.controls.export_flowering_button.clicked.connect(self.export_flowering_pdf)
        self.controls.export_image_button.clicked.connect(self.export_image_layout_pdf)
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        self.controls.species_input.returnPressed.connect(self.finalize_selection)
        self.controls.density_input.returnPressed.connect(self.finalize_selection)

    def setup_completer(self):
        completer = QCompleter(self.plant_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.controls.species_input.setCompleter(completer)
        completer.activated.connect(self.on_species_selected)
        self._completer = completer

    def export_flowering_pdf(self):
        species_in_project = list(self.calculate_species_totals().keys())
        if not species_in_project: return
        filename, _ = QFileDialog.getSaveFileName(self, "Sla Bloeikalender op", "", "PDF (*.pdf)")
        if not filename: return
        plant_details_list = [self.db_manager.get_plant_details(name.lower()) for name in species_in_project if self.db_manager.get_plant_details(name.lower()) is not None]
        generate_flowering_pdf(filename, plant_details_list)
        print(f"Bloeikalender opgeslagen: {filename}")

    def export_order_list_pdf(self):
        species_totals = self.calculate_species_totals()
        if not species_totals: return
        filename, _ = QFileDialog.getSaveFileName(self, "Sla Bestellijst op", "", "PDF (*.pdf)")
        if not filename: return
        plant_details_map = {name.lower(): self.db_manager.get_plant_details(name.lower()) for name in species_totals.keys()}
        generate_order_list_pdf(filename, species_totals, plant_details_map)
        print(f"Bestellijst opgeslagen: {filename}")
        
    def export_image_layout_pdf(self):
        species_in_project = list(self.calculate_species_totals().keys())
        if not species_in_project: return
        filename, _ = QFileDialog.getSaveFileName(self, "Sla Afbeeldingenlayout op", "", "PDF (*.pdf)")
        if not filename: return
        plant_details_list = [self.db_manager.get_plant_details(name.lower()) for name in species_in_project if self.db_manager.get_plant_details(name.lower()) is not None]
        generate_image_layout_pdf(filename, plant_details_list)
        print(f"Afbeeldingenlayout opgeslagen: {filename}")

    def on_species_selected(self, species_name):
        details = self.db_manager.get_plant_details(species_name)
        if details:
            plants_per_m2 = details['plants_per_m2'] if details['plants_per_m2'] else 7
            self.controls.density_input.setText(str(plants_per_m2))
            if self.selected_poly_data:
                self.selected_poly_data['plants_per_m2'] = plants_per_m2
                self.update_calculation()
    
    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecteer een DXF-bestand", "", "DXF Files (*.dxf)")
        if not filepath: return
        try:
            ax = self.canvas.ax_tekengebied; ax.clear(); self.polygons_data.clear(); self.selected_poly_data = None
            self.species_color_map.clear(); self.next_color_index = 0
            doc = ezdxf.readfile(filepath); msp = doc.modelspace()
            for entity in msp:
                points = []; entity_type = entity.dxftype()
                if entity_type in ('LWPOLYLINE', 'POLYLINE') and entity.is_closed:
                    if entity_type == 'LWPOLYLINE': points = [(v[0], v[1]) for v in entity.vertices()]
                    elif entity_type == 'POLYLINE': points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                    if points:
                        poly = Polygon(points, closed=True, facecolor='none', edgecolor='black', linewidth=1)
                        ax.add_patch(poly)
                        self.polygons_data.append({'patch': poly, 'vertices': points, 'plants_per_m2': 7, 'species_name': '', 'is_finished': False})
            ax.set_title("Beplantingsplan"); ax.set_aspect('equal', 'box'); ax.autoscale_view(); self.canvas.draw()
            self.update_ui_on_selection(); self.update_order_list()
        except Exception as e: print(f"Fout bij laden: {e}")

    def on_canvas_click(self, event):
        if event.inaxes != self.canvas.ax_tekengebied or event.xdata is None: return
        click_point = (event.xdata, event.ydata); self.update_all_polygon_colors()
        for poly_data in self.polygons_data:
            if is_point_in_polygon(click_point, poly_data['vertices']):
                self.selected_poly_data = poly_data; self.update_ui_on_selection()
                self.selected_poly_data['patch'].set_facecolor('green'); self.selected_poly_data['patch'].set_alpha(0.7)
                self.canvas.draw(); return

    def finalize_selection(self):
        if not self.selected_poly_data: return
        try:
            species_name = self.controls.species_input.text().strip().lower()
            plants_per_m2 = float(self.controls.density_input.text())
            self.selected_poly_data.update({'species_name': species_name, 'plants_per_m2': plants_per_m2, 'is_finished': True})
            if species_name and species_name not in self.species_color_map:
                self.species_color_map[species_name] = self.COLOR_CYCLE[self.next_color_index]
                self.next_color_index = (self.next_color_index + 1) % len(self.COLOR_CYCLE)
            self.update_all_polygon_colors(); self.update_order_list()
        except ValueError: print("Ongeldige invoer bij 'Planten per m²'")
        except Exception as e: print(f"Fout bij finaliseren: {e}")

    def update_ui_on_selection(self):
        if self.selected_poly_data:
            self.controls.species_input.setText(self.selected_poly_data['species_name'])
            self.controls.density_input.setText(str(self.selected_poly_data['plants_per_m2']))
            self.update_calculation()
        else:
            self.controls.species_input.clear(); self.controls.density_input.clear()
            self.controls.area_label.setText("Oppervlakte: -- m²"); self.controls.plants_label.setText("Aantal planten: --")

    def update_calculation(self):
        if not self.selected_poly_data: return
        area = calculate_polygon_area(self.selected_poly_data['vertices'])
        self.controls.area_label.setText(f"Oppervlakte: {area:.2f} m²")
        try:
            plants_per_sqm = float(self.controls.density_input.text())
            self.controls.plants_label.setText(f"Aantal planten: {int(area * plants_per_sqm)}")
        except ValueError: self.controls.plants_label.setText("Ongeldige invoer")

    def update_all_polygon_colors(self):
        for poly_data in self.polygons_data:
            if poly_data['is_finished']:
                color = self.species_color_map.get(poly_data['species_name'], 'lightgrey')
                poly_data['patch'].set_facecolor(color); poly_data['patch'].set_alpha(0.6)
            else: poly_data['patch'].set_facecolor('none')
        if self.selected_poly_data:
            self.selected_poly_data['patch'].set_facecolor('green'); self.selected_poly_data['patch'].set_alpha(0.7)
        self.canvas.draw()

    def calculate_species_totals(self):
        species_totals = defaultdict(int)
        for poly_data in self.polygons_data:
            if poly_data['is_finished']:
                area = calculate_polygon_area(poly_data['vertices'])
                plant_count = int(area * float(poly_data['plants_per_m2']))
                species_name = poly_data['species_name'].capitalize() or '(Onbekende soort)'
                species_totals[species_name] += plant_count
        return species_totals

    def update_order_list(self):
        self.controls.order_list_display.clear()
        species_totals = self.calculate_species_totals()
        self.controls.order_list_display.append("<b>Bestellijst:</b>")
        for species, total in sorted(species_totals.items()):
            self.controls.order_list_display.append(f"- {species}: {total} stuks")

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()