import ezdxf
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import math
import json
from typing import List, Tuple, Dict
import os

class AutocompleteEntry(ttk.Entry):
    def __init__(self, parent, completevalues, **kwargs):
        ttk.Entry.__init__(self, parent, **kwargs)
        self.completevalues = completevalues
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = tk.StringVar()
        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Return>", self.selection)
        self.listboxup = False

    def changed(self, name, index, mode):
        if self.var.get() == '':
            if self.listboxup:
                self.listbox.destroy()
                self.listboxup = False
        else:
            words = self.comparison()
            if words:
                if not self.listboxup:
                    self.listbox = tk.Listbox(width=self["width"], height=5)
                    self.listbox.place(x=self.winfo_x() + self.winfo_rootx(),
                                     y=self.winfo_y() + self.winfo_rooty() + self.winfo_height())
                    self.listboxup = True
                self.listbox.delete(0, tk.END)
                for w in words:
                    self.listbox.insert(tk.END, w)
            else:
                if self.listboxup:
                    self.listbox.destroy()
                    self.listboxup = False

    def selection(self, event):
        if self.listboxup:
            self.var.set(self.listbox.get(tk.ACTIVE))
            self.listbox.destroy()
            self.listboxup = False
            self.icursor(tk.END)

    def comparison(self):
        return [w for w in self.completevalues 
                if self.var.get().lower() in w.lower()]

class PlantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Plant Planning Tool")
        self.surfaces = []
        self.current_file = None
        self.selected_surface = None
        
        # Load plant data
        self.load_plant_data()
        
        # Setup GUI
        self.setup_gui()

    def load_plant_data(self):
        """Load plant data from JSON file"""
        try:
            with open('plant_data.json', 'r') as f:
                data = json.load(f)
                self.plants = {plant['id']: plant for plant in data['plants']}
                # Create list of plant names for autocomplete
                self.plant_names = [f"{plant['name']} ({plant['latin_name']})" 
                                  for plant in self.plants.values()]
        except FileNotFoundError:
            messagebox.showerror("Error", "plant_data.json not found!")
            self.plants = {}
            self.plant_names = []

    def setup_gui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # File handling buttons
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.btn_frame, text="Import DXF", command=self.import_dxf).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="Calculate Areas", command=self.calculate_areas).pack(side=tk.LEFT, padx=5)

        # Search frame
        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.search_frame, text="Search Plant:").pack(side=tk.LEFT, padx=5)
        self.search_entry = AutocompleteEntry(self.search_frame, self.plant_names, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.handle_plant_selection())
        
        # Canvas for drawing
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Add scrollbars
        self.x_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.y_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(xscrollcommand=self.x_scrollbar.set, yscrollcommand=self.y_scrollbar.set)

    def import_dxf(self):
        """Import DXF file"""
        file_path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
        if file_path:
            self.current_file = ezdxf.readfile(file_path)
            messagebox.showinfo("Success", "DXF file imported successfully")
            self.draw_dxf()

    def draw_dxf(self):
        """Draw the DXF file on the canvas"""
        self.canvas.delete("all")
        if not self.current_file:
            return
        
        msp = self.current_file.modelspace()
        for entity in msp:
            if entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                screen_points = self.convert_to_screen_coords(points, 
                                                              self.canvas.winfo_width(), 
                                                              self.canvas.winfo_height(), 
                                                              50)
                self.canvas.create_polygon(screen_points, outline='black', fill='', tags='dxf')

    def convert_to_screen_coords(self, points, canvas_width, canvas_height, margin):
        """Convert drawing coordinates to screen coordinates"""
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        
        scale_x = (canvas_width - 2 * margin) / (max_x - min_x)
        scale_y = (canvas_height - 2 * margin) / (max_y - min_y)
        scale = min(scale_x, scale_y)
        
        screen_points = []
        for x, y in points:
            screen_x = margin + (x - min_x) * scale
            screen_y = canvas_height - (margin + (y - min_y) * scale)
            screen_points.append((screen_x, screen_y))
        
        return screen_points

    def calculate_areas(self):
        """Calculate areas of all closed polygons"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please import a DXF file first")
            return
            
        msp = self.current_file.modelspace()
        self.surfaces = []
        
        for entity in msp:
            if entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                area = self.calculate_polygon_area(points)
                self.surfaces.append({
                    'points': points,
                    'area': area,
                    'plant': None
                })
                
        messagebox.showinfo("Areas Calculated", 
                          f"Found {len(self.surfaces)} surfaces\n" +
                          "\n".join([f"Surface {i+1}: {s['area']:.2f} m²" 
                                   for i, s in enumerate(self.surfaces)]))
        self.draw_dxf()  # Redraw with updated information

    def calculate_polygon_area(self, points: List[Tuple[float, float]]) -> float:
        """Calculate area of a polygon using shoelace formula"""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        area = abs(area) / 2.0
        return area

    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if not self.surfaces:
            messagebox.showinfo("Info", "Please calculate areas first")
            return
            
        # Convert canvas coordinates to drawing coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked surface
        for i, surface in enumerate(self.surfaces):
            # Convert surface points to screen coordinates
            screen_points = self.convert_to_screen_coords(surface['points'], 
                                                        self.canvas.winfo_width(), 
                                                        self.canvas.winfo_height(), 
                                                        50)
            
            # Check if click is inside polygon
            if self.point_in_polygon(canvas_x, canvas_y, screen_points):
                self.selected_surface = i
                # Highlight selected surface
                self.draw_dxf()
                self.canvas.create_polygon(screen_points, 
                                        outline='blue', 
                                        fill='light blue', 
                                        stipple='gray50',
                                        tags=f'surface_{i}')
                
                # Show area information
                messagebox.showinfo("Surface Selected", 
                                  f"Surface {i+1}\nArea: {surface['area']:.2f} m²")
                return

    def point_in_polygon(self, x, y, polygon_points):
        """Check if point is inside polygon"""
        n = len(polygon_points) // 2
        inside = False
        j = n - 1
        for i in range(n):
            if (((polygon_points[i*2+1] > y) != (polygon_points[j*2+1] > y)) and
                (x < (polygon_points[j*2] - polygon_points[i*2]) * (y - polygon_points[i*2+1]) /
                     (polygon_points[j*2+1] - polygon_points[i*2+1]) + polygon_points[i*2])):
                inside = not inside
            j = i
        return inside

    def handle_plant_selection(self):
        """Handle plant selection from autocomplete"""
        if self.selected_surface is None:
            messagebox.showinfo("Info", "Please select a surface first")
            return
            
        selected_text = self.search_entry.var.get()
        selected_plant = None
        
        # Find selected plant in database
        for plant in self.plants.values():
            if f"{plant['name']} ({plant['latin_name']})" == selected_text:
                selected_plant = plant
                break
                
        if selected_plant:
            surface = self.surfaces[self.selected_surface]
            surface['plant'] = selected_plant
            
            # Calculate plants needed
            area = surface['area']
            plants_needed = math.ceil(area * selected_plant['plants_per_m2'])
            
            # Show information
            info = f"""Surface {self.selected_surface + 1}:
Area: {area:.2f} m²
Plant: {selected_plant['name']}
Plants needed: {plants_needed}
Height: {selected_plant['height_cm']} cm
Blooming months: {', '.join(str(m) for m in selected_plant['blooming_months'])}"""
            
            messagebox.showinfo("Plant Assignment", info)
            
            # Export to Excel
            self.export_to_excel(self.selected_surface, selected_plant)

    def export_to_excel(self, surface_id: int, plant: Dict):
        """Export surface and plant information to Excel"""
        if not self.surfaces or surface_id >= len(self.surfaces):
            return
            
        surface = self.surfaces[surface_id]
        
        data = {
            'Surface Area (m²)': [surface['area']],
            'Plant Name': [plant['name']],
            'Latin Name': [plant['latin_name']],
            'Plants Required': [math.ceil(surface['area'] * plant['plants_per_m2'])],
            'Height (cm)': [plant['height_cm']],
            'Blooming Months': [', '.join(str(m) for m in plant['blooming_months'])],
            'Description': [plant['description']]
        }
        
        df = pd.DataFrame(data)
        filename = f'planting_plan_surface_{surface_id + 1}.xlsx'
        df.to_excel(filename, index=False)
        messagebox.showinfo("Export Complete", f"Data exported to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlantApp(root)
    root.mainloop()