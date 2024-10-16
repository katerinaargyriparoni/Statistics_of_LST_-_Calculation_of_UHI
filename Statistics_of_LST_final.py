import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from shapely.geometry import Point
import matplotlib.pyplot as plt
import os

# Ορισμός διαδρομών
root_path = "/Users/katerinaargyriparoni/data/Madrid/"
urban_shapefile_path = root_path + "madrid_urban.shp"
rural_shapefile_path = root_path + "madrid_rural.shp"

# Φόρτωση γεωμετριών από τα shapefiles
urban_geometries = gpd.read_file(urban_shapefile_path)
rural_geometries = gpd.read_file(rural_shapefile_path)

# Δημιουργία λίστας για αποθήκευση αποτελεσμάτων
results = []

# Συνάρτηση για δημιουργία τυχαίων σημείων εντός του πολύγωνου
def random_points_in_bounds(polygon, num_points):
    minx, miny, maxx, maxy = polygon.bounds
    points = []
    while len(points) < num_points:
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        new_point = Point(x, y)
        if new_point.within(polygon):
            points.append(new_point)
    return points

# Βρείτε όλα τα tif αρχεία σε υποφακέλους
for dirpath, dirnames, filenames in os.walk(os.path.join(root_path, "LST_per_year_clipped")):
    for file in filenames:
        if file.endswith('.tif'):
            image_path = os.path.join(dirpath, file)
            print(f"Επεξεργασία: {image_path}")  # Εμφάνιση της τρέχουσας εικόνας

            # Φόρτωση της εικόνας με τη σωστή μέθοδο
            with rasterio.open(image_path) as src:
                scale = src.scales[0] if src.scales else 1.0
                offset = src.offsets[0] if src.offsets else 0.0
                img = src.read(1).astype(src.dtypes[0])  # Διαβάζουμε την εικόνα
                img = img * scale + offset  # Εφαρμογή του scaling και του offset
                img[img == -32768] = np.nan  # Αντικατάσταση no-data τιμών με NaN

                # Δημιουργία λίστας για να αποθηκεύσετε τις τιμές και τα σημεία
                urban_values = []
                rural_values = []
                urban_points_all = []  # Λίστα για τα τυχαία σημεία urban
                rural_points_all = []  # Λίστα για τα τυχαία σημεία rural

                # Δειγματοληψία urban περιοχών
                for geom in urban_geometries.geometry:
                    urban_points = random_points_in_bounds(geom, 500)
                    urban_points_all.extend(urban_points)  # Προσθήκη σημείων στη λίστα
                    for pt in urban_points:
                        value = img[src.index(pt.x, pt.y)]
                        if not np.isnan(value):
                            urban_values.append(value)  # Προσθήκη τιμής στη λίστα
                    print(f"Δημιουργήθηκαν σημεία urban: {len(urban_points)}")

                # Δειγματοληψία rural περιοχών
                for geom in rural_geometries.geometry:
                    rural_points = random_points_in_bounds(geom, 500)
                    rural_points_all.extend(rural_points)  # Προσθήκη σημείων στη λίστα
                    for pt in rural_points:
                        value = img[src.index(pt.x, pt.y)]
                        if not np.isnan(value):
                            rural_values.append(value)  # Προσθήκη τιμής στη λίστα
                    print(f"Δημιουργήθηκαν σημεία rural: {len(rural_points)}")

                # Υπολογισμός μέσων τιμών και Urban Heat Island
                urban_mean = np.mean(urban_values) if urban_values else np.nan  # Μέση θερμοκρασία για αστικές περιοχές
                rural_mean = np.mean(rural_values) if rural_values else np.nan  # Μέση θερμοκρασία για αγροτικές περιοχές
                uhi = urban_mean - rural_mean if not np.isnan(urban_mean) and not np.isnan(rural_mean) else np.nan  # Υπολογισμός UHI

                # Αποθήκευση αποτελεσμάτων σε DataFrame
                results.append({
                    "image": image_path,
                    "urban_mean": urban_mean,
                    "rural_mean": rural_mean,
                    "UHI": uhi
                })

# Μετατροπή σε DataFrame για εύκολη ανάλυση
results_df = pd.DataFrame(results)

# Ορισμός διαδρομής για την εξαγωγή του CSV
output_csv_path = os.path.join(root_path, "LST_per_year_clipped", "results_summary.csv")
results_df.to_csv(output_csv_path, index=False)

# Υπολογισμός και εκτύπωση βασικών στατιστικών για τις θερμοκρασίες αστικών περιοχών
print("Στατιστικά Αποτελέσματα για τις Θερμοκρασίες Urban:")
print(results_df["urban_mean"].describe())  # Εμφάνιση στατιστικών για αστικές τιμές

# Υπολογισμός και εκτύπωση βασικών στατιστικών για τις θερμοκρασίες αγροτικών περιοχών
print("\nΣτατιστικά Αποτελέσματα για τις Θερμοκρασίες Rural:")
print(results_df["rural_mean"].describe())  # Εμφάνιση στατιστικών για αγροτικές τιμές

print("Περιεχόμενο του DataFrame Αποτελεσμάτων:")
print(results_df)  # Εκτύπωση του περιεχομένου του DataFrame αποτελεσμάτων

# Plotting των τυχαίων σημείων
plt.figure(figsize=(10, 10))
# Plot urban points
if urban_points_all:
    urban_x = [pt.x for pt in urban_points_all]
    urban_y = [pt.y for pt in urban_points_all]
    plt.scatter(urban_x, urban_y, color='blue', label='Urban Points', alpha=0.5)

# Plot rural points
if rural_points_all:
    rural_x = [pt.x for pt in rural_points_all]
    rural_y = [pt.y for pt in rural_points_all]
    plt.scatter(rural_x, rural_y, color='green', label='Rural Points', alpha=0.5)

# Plotting των γεωμετριών
urban_geometries.plot(ax=plt.gca(), edgecolor='blue', facecolor='none', label='Urban Area')
rural_geometries.plot(ax=plt.gca(), edgecolor='green', facecolor='none', label='Rural Area')

plt.title('Τυχαία Σημεία μέσα σε Αστικές και Αγροτικές Περιοχές')
plt.xlabel('Γεωγραφικό Μήκος')
plt.ylabel('Γεωγραφικό Πλάτος')
plt.legend()
plt.grid()
plt.show()





