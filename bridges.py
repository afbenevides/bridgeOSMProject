import requests
import pandas as pd
import folium
import matplotlib.pyplot as plt
from selenium import webdriver
from PIL import Image
import time
import os

# Définition des paramètres
COUNTRY = "Canada"  # Pays
TOWN = "Laval"  # Ville
BRIDGE_TYPE = None  # Mettre "viaduct", "suspension", etc., ou None pour tous les ponts

# Requête Overpass API
query = f"""
[out:json][timeout:60];
area[name="{COUNTRY}"]->.country;
area[name="{TOWN}"](area.country)->.town;
(
  node["bridge"](area.town);
  way["bridge"](area.town);
  relation["bridge"](area.town);
);
out center;
"""

# Récupération des données depuis OpenStreetMap
url = "https://overpass-api.de/api/interpreter"
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()["elements"]

    bridge_data = []

    for idx, element in enumerate(data, start=1):
        tags = element.get("tags", {})
        bridge_type = tags.get("bridge", "unknown")
        lat = element.get("lat") if "lat" in element else element.get("center", {}).get("lat")
        lon = element.get("lon") if "lon" in element else element.get("center", {}).get("lon")
        bridge_id = element.get("id")
        name = tags.get("name", f"Pont #{idx}")

        # Filtrage par type de pont
        if BRIDGE_TYPE and bridge_type.lower() != BRIDGE_TYPE.lower():
            continue

        if lat and lon:
            bridge_data.append({
                "Index": idx,
                "ID": bridge_id,
                "Nom": name,
                "Type": bridge_type,
                "Latitude": lat,
                "Longitude": lon
            })

    # Conversion en DataFrame
    df = pd.DataFrame(bridge_data)

    if not df.empty:
        # Création de la carte centrée sur la ville
        m = folium.Map(location=[df["Latitude"].mean(), df["Longitude"].mean()], zoom_start=13)

        # Ajout des ponts sur la carte avec des cercles rouges en pointillé
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=6,
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.5,
                dash_array="5,5"
            ).add_to(m)

            # Ajout d'une bulle avec les informations du pont
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"{row['Nom']}<br>Type: {row['Type']}<br>Lat: {row['Latitude']}, Lon: {row['Longitude']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        # Sauvegarde de la carte sous forme de fichier HTML
        map_html = f"bridges_map_{TOWN}_{COUNTRY}.html"
        m.save(map_html)
        print(f"Carte interactive enregistrée sous '{map_html}'. Ouvrez le fichier dans un navigateur.")

        # Capture de la carte en image PNG avec Selenium
        map_png = f"bridges_map_{TOWN}_{COUNTRY}.png"

        # Lancement de Selenium WebDriver (assurez-vous que ChromeDriver est installé)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1200x800")

        driver = webdriver.Chrome(options=options)
        driver.get(f"file://{os.path.abspath(map_html)}")

        # Attendre que la carte charge complètement
        time.sleep(3)

        # Capture d'écran et recadrage
        driver.save_screenshot(map_png)
        driver.quit()

        # Chargement et recadrage de l'image avec PIL
        img = Image.open(map_png)
        cropped_img = img.crop((0, 100, 1200, 700))  # Ajustez les dimensions si nécessaire
        cropped_img.save(map_png)

        print(f"Carte statique enregistrée sous '{map_png}'. Ouvrez l'image pour voir les ponts.")

        # Affichage de la table des ponts
        import ace_tools as tools

        tools.display_dataframe_to_user(name="Liste des Ponts", dataframe=df)

    else:
        print(f"Aucun pont trouvé à {TOWN}, {COUNTRY}.")
else:
    print(f"Erreur lors de la récupération des données : {response.status_code}")
