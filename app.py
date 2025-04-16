import pandas as pd
import plotly.express as px
import streamlit as st
import json
import requests
import unicodedata

df = pd.read_csv('C:/Users/Usuario/Documents/Diplomados/Tripleten/Proyectos/Sprint_7/Turismo-internacional/Base_publica_EVI_Aereo.csv', encoding='latin1', sep=';', decimal=",") # leer los datos

# Mapear nombres personalizados en la columna
tipo_map = {
    "Salidas": "No residentes",
    "Llegadas": "Residentes"
}
df["Tipo_Label"] = df["Tipo"].map(tipo_map)

hist_button = st.button('Construir histograma') # crear un botón
scat_button = st.button('Construir scatterplot') # crear un botón
mapa_button = st.button('Construir mapa') # crear un botón
        
if hist_button: # al hacer clic en el botón
    st.write('Creación de un histograma para gasto total por tipo de viaje')

    # crear un histograma
    fig = px.histogram(
    df,
    x="Gasto_tot",
    color="Tipo_Label",
    nbins=50,  # puedes ajustar la cantidad de bins
    marginal="box",  # opcional: muestra boxplot en el margen superior
    opacity=0.7,
    labels={"Gasto_tot": "Gasto Total"},
    title="Distribución del Gasto Total por Tipo de Viaje"
    )

    # mostrar un gráfico Plotly interactivo
    st.plotly_chart(fig, use_container_width=True)


if scat_button: # al hacer clic en el botón
    st.write('Creación de un gráfico de dispersión')

    # crear un histograma
    fig = px.scatter(df, x="Noches", y="Gasto_tot",
                     title="Relación entre Número de Noches y Gasto Total",
                     labels={"Noches": "Número de Noches",
                             "Gasto_tot": "Gasto Total (COP)"
                             })

    # mostrar un gráfico Plotly interactivo
    st.plotly_chart(fig, use_container_width=True)

# --- Normalización ---
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

# --- Datos y filtros ---
df_salida = df[df["Tipo"] == "Salidas"].copy()

# Correcciones manuales
correcciones = {
    "Bogotá, D.C.": "Santafe De Bogota D.C",
    "San Andrés y Prov.": "Archipielago De San Andres Providencia Y Santa Catalina",
    "San Andrés Y Providencia": "Archipielago De San Andres Providencia Y Santa Catalina",
    "Norte De Santander": "Norte de Santander",
    "Valle Del Cauca": "Valle del Cauca",
}
df_salida["Per_prin"] = df_salida["Per_prin"].replace(correcciones)

# Crear campo normalizado
df_salida["departamento_normalizado"] = df_salida["Per_prin"].apply(remove_accents)

# Agrupar
pernoctacion_departamentos = df_salida.groupby("departamento_normalizado")['fexp'].sum().reset_index(name="Conteo")

# --- GeoJSON ---
url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
geojson = requests.get(url).json()

# Normalizar nombres del GeoJSON
for feature in geojson["features"]:
    nombre_original = feature["properties"]["NOMBRE_DPT"]
    feature["properties"]["departamento_normalizado"] = remove_accents(nombre_original)

# Verificación: ¿todos los nombres del DataFrame están en el GeoJSON?
geojson_deptos = set(f["properties"]["departamento_normalizado"] for f in geojson["features"])
df_deptos = set(pernoctacion_departamentos["departamento_normalizado"])

diferencias = df_deptos - geojson_deptos
if diferencias:
    print("Departamentos no encontrados en GeoJSON:", diferencias)

if mapa_button: # al hacer clic en el botón
    st.write('Creación de mapa de calor con cantidad de turistas')

    # crear un histograma
    fig = px.choropleth(
        pernoctacion_departamentos,
        geojson=geojson,
        locations="departamento_normalizado",
        featureidkey="properties.departamento_normalizado",
        color="Conteo",
        color_continuous_scale="Turbo",
        title="Pernoctaciones principales por departamento",
        labels={"Conteo": "Número de pernoctaciones"}
        )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

    # mostrar un gráfico Plotly interactivo
    st.plotly_chart(fig, use_container_width=True)
