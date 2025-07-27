import os
import requests
import zipfile
import pandas as pd
from pymongo import MongoClient

# 1. Descargar el ZIP
url = 'https://netsg.cs.sfu.ca/youtubedata/0302.zip'  # actualizado a 0302.zip
zip_path = '0302.zip'
with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with open(zip_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
print("ZIP descargado:", zip_path)

# 2. Descomprimir en carpeta
extract_dir = 'youtube_data'
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_dir)
print("Archivos extraídos en:", extract_dir)

# 3. Buscar archivos .txt dentro del subdirectorio 0302
sub_dir = os.path.join(extract_dir, '0302')
files = os.listdir(sub_dir)
print("Archivos disponibles en 0302:", files)

# 4. Leer el primer archivo .txt real (por ejemplo, '0.txt')
txt_files = [f for f in files if f.endswith('.txt') and f != 'log.txt']
if not txt_files:
    raise FileNotFoundError(f"No se encontraron archivos .txt válidos en {sub_dir}")

file0 = os.path.join(sub_dir, txt_files[0])
df = pd.read_csv(file0, sep='\t', header=None)

# 5.1 Renombrar columnas según descripción:
col_names = ['VideoID','uploader','age','category','length','views','rate','ratings','comments'] + \
            [f'related{i}' for i in range(df.shape[1] - 9)]
df.columns = col_names

# 6. Seleccionar columnas relevantes
df2 = df[['VideoID', 'age', 'category', 'views', 'rate']].copy()

# 6.1 Filtrado básico: solo categorías 'Entertainment' o 'Music'
df2 = df2[df2['category'].isin(['Entertainment', 'Music'])]
print("Data filtrada:", df2.shape)

# Mostrar primeras 5 filas
print(df2.head())

# 7. Exportar a MongoDB Atlas
mongo_uri = "mongodb+srv://carlosaquino3501:lHu0nlmMt4zdR0g2@dev.uk2uy6b.mongodb.net/?retryWrites=true&w=majority&appName=Dev"
cliente = MongoClient(mongo_uri)
try:
    cliente.admin.command('ping')
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print("Error de conexión a MongoDB:", e)
    exit(1)

db = cliente['youtube_data']
col = db['videos0302']
col.insert_many(df2.to_dict(orient='records'))
print("Insertados en MongoDB colección videos0302, total:", col.count_documents({}))

# 8. Mostrar link (ejemplo de cómo lo compartirías/documentarías)
print("Encontrás los datos en tu cluster de MongoDB Atlas bajo:\n"
      "Base: youtube_data a colección: videos0302\n"
      "Puedes acceder desde Compass o tu dashboard de Atlas.")
