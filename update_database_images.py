# update_database_images.py
import sqlite3

# Deze dictionary is nu bijgewerkt met de bestandsnamen uit jouw screenshot.
# De namen links komen (in kleine letters) uit het create_database.py script.
image_map = {
    'aster "little carlow"': 'plant_images/aster_little_carlow.jpg',
    'calamintha nepeta ssp. nepeta': 'plant_images/calamintha.jpg',
    'echinops bannaticus "taplow blue"': 'plant_images/echinops.jpg',
    'geranium x oxonianum "rose clair"': 'plant_images/Geranium.jpg',
    'salvia nemerosa "schneehugel"': 'plant_images/salvia_schneehugel.jpg'
}

try:
    conn = sqlite3.connect('planten.db')
    cursor = conn.cursor()
    
    updates_succesvol = 0
    for name, path in image_map.items():
        # Zoek de plant op naam (ongeacht hoofdletters) en update het image_path veld.
        cursor.execute("UPDATE plants SET image_path = ? WHERE LOWER(name) = ?", (path, name))
        if cursor.rowcount > 0:
            print(f"Pad voor '{name}' bijgewerkt naar '{path}'")
            updates_succesvol += 1
        else:
            print(f"WAARSCHUWING: Plant '{name}' niet gevonden in de database.")

    conn.commit()
    conn.close()
    
    print(f"\nDatabase bijgewerkt. {updates_succesvol} afbeeldingspaden succesvol ingesteld.")

except sqlite3.Error as e:
    print(f"Een databasefout is opgetreden: {e}")