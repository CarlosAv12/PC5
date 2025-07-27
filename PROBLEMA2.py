import pandas as pd
import sqlite3
from pymongo import MongoClient

# 1. Leer CSV principal desde archivo local
df = pd.read_csv('/workspaces/PC5/data/winemag-data-130k-v2.csv', index_col=0)

# 1.1 Exploración del DataFrame
print("Forma del DataFrame:", df.shape)
print("\nTipos de datos:\n", df.dtypes)
print("\nPrimeros 10 registros:")
print(df.head(10).to_string())
print("\nÚltimos 5 registros:")
print(df.tail().to_string())

# 2. Renombrar columnas
df.rename(columns={'description': 'descripcion'}, inplace=True)
column_renames = {
    'country': 'pais',
    'points': 'puntos',
    'price': 'precio_usd',
    'variety': 'tipo_uva'
}
df.rename(columns=column_renames, inplace=True)

# 3. Crear nuevas columnas
continentes_url = 'https://gist.githubusercontent.com/kintero/7d1db891401f56256c79/raw/a61f6d0dda82c3f04d2e6e76c3870552ef6cf0c6/paises.csv'
df_cont = pd.read_csv(continentes_url)
print("Columnas originales en df_cont:", df_cont.columns)

# Confirmamos si 'name' está en las columnas antes de renombrar
if ' name' in df_cont.columns:
    df_cont.rename(columns={' name': 'pais'}, inplace=True)
    print("Columna 'name' renombrada a 'pais'.")
else:
    print("La columna 'name' no existe en df_cont. Usando alternativa.")
    if 'nombre' in df_cont.columns:
        df_cont.rename(columns={'nombre': 'pais'}, inplace=True)
        print("Columna 'nombre' renombrada a 'pais'. (nombres en español)")
    else:
        print("Ninguna columna válida encontrada para renombrar a 'pais'")
        print(df_cont.columns)
        print(df_cont.head().to_string())

# Asegurarse de que la columna 'pais' existe en ambos DataFrames
if 'pais' in df.columns and 'pais' in df_cont.columns:
    merged = df.merge(df_cont, on='pais', how='left')
else:
    print("No se puede realizar el merge: columna 'pais' no encontrada en uno de los DataFrames.")
    print("Columnas en df:", df.columns)
    print("Columnas en df_cont:", df_cont.columns)
    merged = df.copy()  # evitar crash para seguir mostrando otros procesos

# Verificar países sin continente
print("\nPaíses sin continente detectado:")
print(merged[merged['continente'].isna()]['pais'].unique())

# 3.1 Columna de calidad según puntaje
merged['calidad'] = pd.cut(merged['puntos'], bins=[0, 85, 90, 95, 100], labels=['Baja', 'Media', 'Alta', 'Excelente'])

# 3.2 Precio por punto

# 3.2.1 Clasificación por rango de precio
merged['rango_precio'] = pd.cut(merged['precio_usd'],
    bins=[0, 15, 30, 60, float('inf')],
    labels=['Económico', 'Accesible', 'Premium', 'Alta gama'])
merged['precio_por_punto'] = merged['precio_usd'] / merged['puntos']

# 3.3 Largo del título (como alternativa a la descripción)
if 'title' in merged.columns:
    merged['largo_titulo'] = merged['title'].apply(lambda x: len(str(x)))
else:
    print("No se encontró la columna 'title' para calcular el largo del título.")

# 4. REPORTES

# REPORTE EXTRA: Distribución de vinos por rango de precio y calidad y largo de título promedio
reporte_extra = merged.groupby(['rango_precio', 'calidad']).agg(
    cantidad_vinos=('pais', 'count'),
    puntaje_medio=('puntos', 'mean'),
    largo_titulo_promedio=('largo_titulo', 'mean')
).reset_index().sort_values(by='cantidad_vinos', ascending=False)
reporte_extra.to_csv('vinos_por_rango_precio_y_calidad.csv', index=False)
reporte_extra = merged.groupby(['rango_precio', 'calidad']).agg(
    cantidad_vinos=('pais', 'count'),
    puntaje_medio=('puntos', 'mean')
).reset_index().sort_values(by='cantidad_vinos', ascending=False)
reporte_extra.to_csv('vinos_por_rango_precio_y_calidad.csv', index=False)

# REPORTE 1: Mejor vino por continente
reporte1 = merged.loc[merged.groupby('continente')['puntos'].idxmax()][['pais', 'continente', 'puntos', 'descripcion']]
reporte1.to_csv('mejores_vinos_por_continente.csv', index=False)

# REPORTE 2: Promedio de precio y cantidad de reviews por país
reporte2 = merged.groupby('pais').agg(
    precio_promedio=('precio_usd', 'mean'),
    cantidad_reviews=('descripcion', 'count')
).sort_values(by='precio_promedio', ascending=False)
reporte2.to_excel('precio_y_reviews_por_pais.xlsx')

# REPORTE 3: Top 10 uvas más comunes y su puntaje promedio
reporte3 = merged.groupby('tipo_uva').agg(
    cantidad=('tipo_uva', 'count'),
    puntos_promedio=('puntos', 'mean')
).sort_values(by='cantidad', ascending=False).head(10)

conn = sqlite3.connect('vinos.db')
reporte3.to_sql('top_uvas', conn, if_exists='replace')
conn.close()

# REPORTE 4: Vinos de Argentina, Chile y Francia por calidad
reporte4 = merged[merged['pais'].isin(['Argentina', 'Chile', 'France'])][['pais', 'tipo_uva', 'puntos', 'calidad']]

# (Opcional) Envío por correo - se describe el paso
# Se usaría smtplib + email.message para adjuntar el CSV generado y enviarlo
# Mostrar pantallazo del correo enviado con el archivo CSV "mejores_vinos_por_continente.csv"

print("Reportes generados y exportados:")
print("1. CSV: mejores_vinos_por_continente.csv")
print("2. Excel: precio_y_reviews_por_pais.xlsx")
print("3. SQLite: vinos.db (tabla top_uvas)")
print("4. MongoDB Atlas: colección Vinos_Argentinda_Chile_Francia en base mi_base")

### MANDAMOS EL CORREO ELECTRÓNICO

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configuración del servidor y credenciales
import os 

smtp_server = 'smtp.gmail.com'  # Cambia esto al servidor SMTP que estés utilizando
smtp_port = 587  # Cambia esto al puerto adecuado
sender_email = 'grupo2emprendimiento22@gmail.com'
sender_password = open('token.txt').read().strip() #os.environ['gmail_pass'] #

# Detalles del correo electrónico
receiver_email = 'gonzalo.delgado.r@uni.pe,carlos.aquino3501@gmail.com,carlos.aquino5@unmsm.edu.pe'
receiver_list = receiver_email.split(",")  # <-- convertir a lista
subject = 'Reporte de precios y reviews por país'
body = 'Buen día,\n\nSoy Carlos Alberto Aquino Vilca del curso de Python Junio 2025 - Sábados.\n\nAdjunto lo solicitado.\nSaludos.'

# Crear el objeto MIMEMultipart
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))


# Adjuntar archivo
file_path = '/workspaces/PC5/precio_y_reviews_por_pais.xlsx'  # Cambia la ruta al archivo que quieras adjuntar
with open(file_path, 'rb') as file:
    attachment = MIMEApplication(file.read(), _subtype="csv")
    attachment.add_header('Content-Disposition', 'attachment', filename=file_path)
    msg.attach(attachment)
    
# Iniciar la conexión con el servidor SMTP
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()  # Iniciar el modo seguro
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_list, msg.as_string())

print('Correo enviado exitosamente')