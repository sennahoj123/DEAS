import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button, TextBox
import ezdxf
import tkinter as tk
from tkinter import filedialog
from matplotlib.patches import Polygon
import numpy as np
from collections import defaultdict

# LIJST MET KLEUREN
COLOR_CYCLE = [
    '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462',
    '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f'
]

# --- HULPFUNCTIES ---
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

# --- GLOBALE VARIABELEN ---
g_polygons_data = []
g_selected_poly_data = None 
g_species_color_map = {}
g_next_color_index = 0
g_order_list_texts = [] 

# SETUP BESTANDSVENSTER
root = tk.Tk(); root.withdraw()

def select_file(event):
    filepath = filedialog.askopenfilename(title="Selecteer een DXF-bestand", filetypes=(("DXF Files", "*.dxf"),))
    if not filepath: return
    try:
        ax_tekengebied.clear(); g_polygons_data.clear()
        global g_selected_poly_data, g_species_color_map, g_next_color_index
        g_selected_poly_data = None; g_species_color_map = {}; g_next_color_index = 0
        text_result_area.set_text("Oppervlakte: -- m²"); text_result_plants.set_text("Aantal planten: --")
        textbox_species.set_val(''); textbox_plants.set_val('7')
        update_order_list()
        doc = ezdxf.readfile(filepath); msp = doc.modelspace()
        for entity in msp:
            points = []; entity_type = entity.dxftype()
            if entity_type in ('LWPOLYLINE', 'POLYLINE') and entity.is_closed:
                if entity_type == 'LWPOLYLINE': points = [(v[0], v[1]) for v in entity.vertices()]
                elif entity_type == 'POLYLINE': points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                if points:
                    poly = Polygon(points, closed=True, facecolor='none', edgecolor='black', linewidth=1)
                    ax_tekengebied.add_patch(poly)
                    g_polygons_data.append({'patch': poly, 'vertices': points, 'plants_per_m2': 7, 'species_name': '', 'is_finished': False})
        ax_tekengebied.set_title("Beplantingsplan"); ax_tekengebied.set_aspect('equal', 'box')
        ax_tekengebied.autoscale_view(); fig.canvas.draw_idle()
    except Exception as e: print(f"Een fout is opgetreden: {e}")

def on_click(event):
    if event.inaxes != ax_tekengebied or event.xdata is None: return
    click_point = (event.xdata, event.ydata)
    global g_selected_poly_data
    if g_selected_poly_data:
        if not g_selected_poly_data['is_finished']:
             g_selected_poly_data['patch'].set_facecolor('none')
        else:
            species = g_selected_poly_data['species_name']
            if species in g_species_color_map:
                g_selected_poly_data['patch'].set_facecolor(g_species_color_map[species]); g_selected_poly_data['patch'].set_alpha(0.6)
            else:
                g_selected_poly_data['patch'].set_facecolor('royalblue'); g_selected_poly_data['patch'].set_alpha(0.6)

    for poly_data in g_polygons_data:
        if is_point_in_polygon(click_point, poly_data['vertices']):
            g_selected_poly_data = poly_data
            textbox_plants.set_val(g_selected_poly_data['plants_per_m2'])
            textbox_species.set_val(g_selected_poly_data['species_name'])
            update_calculation()
            g_selected_poly_data['patch'].set_facecolor('green'); g_selected_poly_data['patch'].set_alpha(0.7)
            fig.canvas.draw_idle()
            return

def update_calculation():
    if not g_selected_poly_data: return
    area = calculate_polygon_area(g_selected_poly_data['vertices'])
    text_result_area.set_text(f"Oppervlakte: {area:.2f} m²")
    try:
        plants_per_sqm = float(g_selected_poly_data['plants_per_m2'])
        total_plants = int(area * plants_per_sqm)
        text_result_plants.set_text(f"Aantal planten: {total_plants}")
    except ValueError: text_result_plants.set_text("Ongeldige invoer")

def on_submit_plants(text):
    if not g_selected_poly_data: return
    try:
        g_selected_poly_data['plants_per_m2'] = float(text)
        g_selected_poly_data['is_finished'] = True
        update_all_polygon_colors()
        update_order_list()
    except ValueError: print("Ongeldige invoer.")

def on_submit_species(text):
    if not g_selected_poly_data: return
    g_selected_poly_data['species_name'] = text.strip().lower()
    g_selected_poly_data['is_finished'] = True
    global g_next_color_index
    species_name = g_selected_poly_data['species_name']
    if species_name and species_name not in g_species_color_map:
        g_species_color_map[species_name] = COLOR_CYCLE[g_next_color_index]
        g_next_color_index = (g_next_color_index + 1) % len(COLOR_CYCLE)
    update_all_polygon_colors()
    update_order_list()

def update_all_polygon_colors():
    for poly_data in g_polygons_data:
        if poly_data['is_finished']:
            species = poly_data['species_name']
            if species in g_species_color_map:
                poly_data['patch'].set_facecolor(g_species_color_map[species]); poly_data['patch'].set_alpha(0.6)
            else:
                poly_data['patch'].set_facecolor('royalblue'); poly_data['patch'].set_alpha(0.6)
        else:
            poly_data['patch'].set_facecolor('none')
    if g_selected_poly_data:
        g_selected_poly_data['patch'].set_facecolor('green'); g_selected_poly_data['patch'].set_alpha(0.7)
    fig.canvas.draw_idle()

def update_order_list():
    for text_obj in g_order_list_texts: text_obj.remove()
    g_order_list_texts.clear()
    species_totals = defaultdict(int)
    for poly_data in g_polygons_data:
        if poly_data['is_finished']:
            try:
                area = calculate_polygon_area(poly_data['vertices'])
                plant_count = int(area * float(poly_data['plants_per_m2']))
                species_name = poly_data['species_name'].capitalize() or '(Onbekende soort)'
                species_totals[species_name] += plant_count
            except (ValueError, KeyError): continue
    y_pos = 0.40
    title_obj = ax_paneel.text(0.1, y_pos, "Bestellijst:", weight='bold', fontsize=12); g_order_list_texts.append(title_obj)
    y_pos -= 0.06
    for species, total in sorted(species_totals.items()):
        display_text = f"- {species}: {total} stuks"
        text_obj = ax_paneel.text(0.1, y_pos, display_text, fontsize=10); g_order_list_texts.append(text_obj)
        y_pos -= 0.05
    fig.canvas.draw_idle()

# --- LAYOUT CODE & WIDGETS ---
fig = plt.figure(figsize=(12, 7)); gs = GridSpec(1, 4, figure=fig)
ax_tekengebied = fig.add_subplot(gs[0, :3]); ax_paneel = fig.add_subplot(gs[0, 3])
ax_tekengebied.set_title("Beplantingsplan"); ax_tekengebied.set_aspect('equal', 'box')
ax_paneel.set_facecolor('#f0f0f0'); ax_paneel.get_xaxis().set_visible(False); ax_paneel.get_yaxis().set_visible(False)
fig.tight_layout(pad=2)
ax_button_load = ax_paneel.inset_axes([0.1, 0.90, 0.8, 0.08]); button_load = Button(ax_button_load, 'Laad DXF'); button_load.on_clicked(select_file)
ax_paneel.text(0.1, 0.82, "Plantsoort:", fontsize=10)
ax_textbox_species = ax_paneel.inset_axes([0.1, 0.76, 0.8, 0.06]); textbox_species = TextBox(ax_textbox_species, '', initial=''); textbox_species.on_submit(on_submit_species)
ax_paneel.text(0.1, 0.68, "Planten per m²:", fontsize=10)
ax_textbox_plants = ax_paneel.inset_axes([0.1, 0.62, 0.8, 0.06]); textbox_plants = TextBox(ax_textbox_plants, '', initial='7'); textbox_plants.on_submit(on_submit_plants)
text_result_area = ax_paneel.text(0.1, 0.54, "Oppervlakte: -- m²", fontsize=11)
text_result_plants = ax_paneel.text(0.1, 0.48, "Aantal planten: --", fontsize=11)
cid_click = fig.canvas.mpl_connect('button_press_event', on_click)
print("Applicatie gestart. Wacht op actie..."); update_order_list()
plt.show()
print("Applicatie is afgesloten.")