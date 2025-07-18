# exporting/pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet

def generate_flowering_pdf(filename, species_details_list):
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    
    months = ["Jan", "Feb", "Maa", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
    header = ["Vaste planten"] + months
    data = [header]
    
    style_commands = [
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,1), (0,-1), 'LEFT'), ('LEFTPADDING', (0,1), (0,-1), 5),
    ]

    for i, plant_info in enumerate(sorted(species_details_list, key=lambda p: p['name'])):
        row_num = i + 1
        row_data = [plant_info['name'].capitalize()] + [''] * 12
        
        struct_start, struct_end = plant_info['structure_start_month'], plant_info['structure_end_month']
        flower_start, flower_end = plant_info['flower_start_month'], plant_info['flower_end_month']

        if struct_start and struct_end:
            for m in range(struct_start, struct_end + 1):
                row_data[m] = 'S'
                style_commands.append(('BACKGROUND', (m, row_num), (m, row_num), colors.HexColor('#d4edbc')))
        
        if flower_start and flower_end:
            for m in range(flower_start, flower_end + 1):
                row_data[m] = 'B'
                style_commands.append(('BACKGROUND', (m, row_num), (m, row_num), colors.HexColor('#bce8f1')))
        
        data.append(row_data)
    
    table = Table(data, colWidths=[6*cm] + [1.9*cm] * 12, rowHeights=0.7*cm)
    table.setStyle(TableStyle(style_commands))
    
    elements.append(table)
    doc.build(elements)

def generate_order_list_pdf(filename, species_totals, plant_details_map):
    c = canvas.Canvas(filename, pagesize=A4); width, height = A4
    c.setFont("Helvetica-Bold", 12); c.drawString(15*cm, height - 2*cm, "DEAS V.O.F")
    c.setFont("Helvetica", 10); c.drawString(15*cm, height - 2.5*cm, "Haldereng 39 6721XR Bennekom"); c.drawString(15*cm, height - 3*cm, "BTW: NL862942111B01 KVK: 836355")
    
    data = [['Omschrijving', 'Kwaliteit', 'Aantal', 'P/eenheid', 'Prijs in euro']]; total_ex_btw = 0
    
    for species, total_amount in sorted(species_totals.items()):
        details = plant_details_map.get(species.lower())
        quality, price = (details['quality'], details['price_per_unit']) if details else ('N/A', 0)
        
        line_total = total_amount * price; total_ex_btw += line_total
        data.append([
            species.capitalize(), quality, str(total_amount), f"€ {price:.2f}", f"€ {line_total:.2f}"
        ])
        
    table = Table(data, colWidths=[8*cm, 2*cm, 2*cm, 2.5*cm, 3*cm])
    style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12)])
    table.setStyle(style); table.wrapOn(c, width, height); table.drawOn(c, 2*cm, height - 8*cm)
    
    btw_9_procent = total_ex_btw * 0.09; total_inc_btw = total_ex_btw + btw_9_procent
    c.setFont("Helvetica-Bold", 12); c.drawRightString(width - 2*cm, height - 12*cm, f"TOTAAL EX. BTW: € {total_ex_btw:.2f}")
    c.setFont("Helvetica", 10); c.drawRightString(width - 2*cm, height - 12.5*cm, f"BTW 9%: € {btw_9_procent:.2f}")
    c.setFont("Helvetica-Bold", 14); c.drawRightString(width - 2*cm, height - 13.5*cm, f"TOTAAL INCL. BTW: € {total_inc_btw:.2f}")
    c.save()

def generate_image_layout_pdf(filename, species_details_list):
    """Genereert een PDF met een grid van plantafbeeldingen en namen."""
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet(); styleN = styles['Normal']; styleN.alignment = 1
    elements = []
    
    cols = 3; table_data = []; row_data = []

    for plant_info in sorted(species_details_list, key=lambda p: p['name']):
        # --- DE CORRECTIE ---
        path = plant_info['image_path'] if 'image_path' in plant_info.keys() else None
        
        if not path:
            continue

        try:
            img = Image(path, width=8*cm, height=6*cm, kind='proportional')
            name_paragraph = Paragraph(plant_info['name'].capitalize(), styleN)
            cell_story = [img, Spacer(1, 0.2*cm), name_paragraph]
            row_data.append(cell_story)
            
            if len(row_data) == cols:
                table_data.append(row_data); row_data = []

        except Exception as e:
            print(f"Kon afbeelding niet laden: {path} - {e}")
            
    if row_data:
        while len(row_data) < cols: row_data.append("")
        table_data.append(row_data)

    if not table_data:
        print("Geen planten met afbeeldingen gevonden om te exporteren."); return

    table = Table(table_data, colWidths=[9*cm]*cols, rowHeights=7*cm)
    table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    elements.append(table)
    doc.build(elements)