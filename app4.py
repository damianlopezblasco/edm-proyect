import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import openpyxl
import requests

# Configuración de la aplicación
st.set_page_config(page_title="Cuidando Valencia", layout="wide")

# Crear las pestañas
tab1, tab2, tab3, tab4 = st.tabs(["Inicio", "Niños y Familias", "Personas Mayores", "Personas con Discapacidad"])

def obtener_datos_valenbici():
    url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/valenbisi-disponibilitat-valenbisi-dsiponibilidad/records?limit=20"
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])

# Obtener los datos
valenbici_data = obtener_datos_valenbici()

# Procesar los datos y crear un DataFrame
data_list = []
for record in valenbici_data:
    fields = record  # La estructura tiene los campos directamente en el registro
    fields['lat'] = fields['geo_shape']['geometry']['coordinates'][1]
    fields['lon'] = fields['geo_shape']['geometry']['coordinates'][0]
    data_list.append(fields)

valenbici_df = pd.DataFrame(data_list)

# Pestaña de Inicio
with tab1:
    st.title("Inicio")
    st.subheader("¡Bienvenidos a nuestra aplicación!")
    st.write("Nos complace anunciar que, según la prestigiosa revista Forbes, Valencia ha sido elegida recientemente como la mejor ciudad para vivir. En reconocimiento a este honor, hemos desarrollado una aplicación innovadora diseñada para ayudar a mantener y mejorar el nivel de vida de nuestros nuevos usuarios en esta maravillosa ciudad. Nuestro objetivo es proporcionar todas las herramientas y recursos necesarios para que puedas disfrutar al máximo de lo que Valencia tiene para ofrecer.")
    st.write("Para más información sobre este emocionante reconocimiento, puedes leer el artículo completo de Forbes en el siguiente enlace: [Forbes - Valencia, la mejor ciudad para vivir](https://forbes.es/lifestyle/89771/valencia-la-mejor-ciudad-del-mundo-para-vivir-segun-una-encuesta-global/)")
    st.subheader("Valenbici")
    st.write("¡Vivir en Valencia tiene muchas ventajas, y una de las más destacadas es la gran disponibilidad de desplazamiento sostenible! Para facilitar tu movilidad, hemos creado este mapa interactivo donde puedes consultar todas las localizaciones de recogida de bicicletas. Aquí podrás ver la disponibilidad de bicicletas y los huecos libres para aparcar, ¡todo en tiempo real! Disfruta de una ciudad más verde y eficiente mientras te desplazas de manera rápida y ecológica.")
    # Crear el mapa de Valenbici
    try:
        m = folium.Map(location=[39.46975, -0.37739], zoom_start=13)

        for _, row in valenbici_df.iterrows():
            direccion = row.get('address', 'Dirección desconocida')
            bicis_disponibles = row.get('available', 'No disponible')
            espacios_libres = row.get('free', 'No disponible')
            lat = row['lat']
            lon = row['lon']

            popup_content = f"""
            <div style="font-size: 14px;">
                <b>{direccion}</b><br>
                <i>Bicicletas disponibles:</i> {bicis_disponibles}<br>
                <i>Espacios libres:</i> {espacios_libres}
            </div>
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=250),
                icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
            ).add_to(m)

        st_folium(m, width=1400, height=700)
    except Exception as e:
        st.error(f"Error al mostrar el mapa de Valenbici: {e}")

# Pestaña de Niños y Familias
with tab2:
    st.title("Niños y Familias")
    st.write("En esta sección encontrarás información para ayudarte con los más pequeños de la casa.")
    st.write("Una vez selecciones un tipo de régimen escolar, aparecerá un mapa mostrando la localización de dichos centros.")

    # Cargar la base de datos de colegios
    colegios_df = pd.read_csv('colegios.csv')
    colecamins_df = pd.read_csv('colecamins.csv')

    # Crear el mapa
    m = folium.Map(location=[colegios_df['Latitud'].mean(), colegios_df['Longitud'].mean()], zoom_start=12)

    # Crear checkboxes para seleccionar el régimen
    st.write("Selecciona el tipo de régimen escolar:")
    public = st.checkbox("PÚBLICO", value=False)
    privado = st.checkbox("PRIVADO", value=False)
    concertado = st.checkbox("CONCERTADO", value=False)

    selected_regimen = []
    if public:
        selected_regimen.append("PÚBLICO")
    if privado:
        selected_regimen.append("PRIVADO")
    if concertado:
        selected_regimen.append("CONCERTADO")

    filtered_colegios = colegios_df[colegios_df['regimen'].isin(selected_regimen)]

    # Añadir puntos al mapa
    color_dict = {"PÚBLICO": "blue", "PRIVADO": "red", "CONCERTADO": "green"}
    for _, row in filtered_colegios.iterrows():
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=row['dlibre'],
            icon=folium.Icon(color=color_dict[row['regimen']])
        ).add_to(m)

    # Añadir desplegable para seleccionar el colegio
    st.write("Algo que puede resultarte muy útil son las rutas \"colecamins\", se trata de ciertas rutas que siguen los alumnos para ir al colegio en grupo de forma segura.")
    colegio_options = colecamins_df['Colegio'].unique()
    colegio_input = st.selectbox("Selecciona un colegio para mostrar sus rutas colecamins:", colegio_options)

    if colegio_input:
        colegio_rows = colecamins_df[colecamins_df['Colegio'] == colegio_input]
        if not colegio_rows.empty:
            st.write(f"Mostrando rutas para {colegio_input}")
            colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred',
                      'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
                      'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray',
                      'black', 'lightgray']
            color_index = 0
            for _, row in colegio_rows.iterrows():
                geo_shape = row['geo_shape']
                geo_shape_dict = ast.literal_eval(geo_shape)
                coordinates = geo_shape_dict['coordinates']
                folium.PolyLine(
                    locations=[(lat, lon) for lon, lat in coordinates],
                    color=colors[color_index % len(colors)]
                ).add_to(m)
                color_index += 1
        else:
            st.write("El colegio introducido no se encuentra en la base de datos.")

    # Checkbox para mostrar parques
    st.write("Otro punto de interés para los niños son los parques y zonas verdes, para ello hemos implementado esta opción que muestra su localización en el mapa.")
    show_parks = st.checkbox("Mostrar parques")

    if show_parks:
        parques_df = pd.read_csv('parques.csv')
        for _, row in parques_df.iterrows():
            folium.Marker(
                location=[row['Latitud'], row['Longitud']],
                popup="Parque",
                icon=folium.Icon(color='green', icon='tree', prefix='fa')
            ).add_to(m)

    # Mostrar el mapa en Streamlit
    st_folium(m, width=1400, height=700)

# Pestaña de Personas Mayores
with tab3:
    st.title("Ayuda Mayores")
    st.write("En esta sección puedes encontrar localizaciones de recursos y asistencia para personas mayores.")
    st.write("También encontrarás información sobre la calidad del aire.")

    # Cargar las bases de datos
    hospitales_df = pd.read_csv('hospitales.csv', encoding='ISO-8859-1')
    calidad_df = pd.read_csv('calidad_hora_a_dia.csv')
    mayores_df = pd.read_excel("majors-mayores2.xlsx")

    # Asegurarse de que la columna 'Fecha' en calidad_df sea de tipo datetime
    calidad_df['Fecha'] = pd.to_datetime(calidad_df['Fecha'], errors='coerce')

    # Crear el mapa
    m = folium.Map(location=[hospitales_df['Latitud'].mean(), hospitales_df['Longitud'].mean()], zoom_start=12)

    # Crear desplegable para seleccionar el barrio
    st.write("Algo que puede resultarte muy útil seria conocer los \"hospitales\" que tiene cerca de su zona.")
    barrios_options = hospitales_df['Barrio'].unique()
    barrio_input = st.selectbox("Selecciona un barrio para mostrar sus diferentes hospitales:", barrios_options)
    st.write("Los colores de los hospitales vienen definidos en función de si es Público(azul),Privado(rojo) y Concertado(verde).")

    if barrio_input:
        hospitales_barrio = hospitales_df[hospitales_df['Barrio'] == barrio_input]
        if not hospitales_barrio.empty:
            st.write(f"Mostrando hospitales en {barrio_input}")
            color_dict = {"Publico": "blue", "Privado": "red", "Concertado": "green"}
            for _, row in hospitales_barrio.iterrows():
                folium.Marker(
                    location=[row['Latitud'], row['Longitud']],
                    popup=row['Nombre'],
                    icon=folium.Icon(color=color_dict.get(row['Financiaci'], 'gray'))
                ).add_to(m)
        else:
            st.write("No se encontraron hospitales en el barrio seleccionado.")
    # Checkbox para mostrar centros de día
    st.write("Otro punto de interés para las personas mayores son los centros de día.")
    show_centros = st.checkbox("Mostrar los centros de día")

    if show_centros:
        for _, row in mayores_df.iterrows():
            folium.Marker(
                location=[row['Latitud'], row['Longitud']],
                popup=row['Nombre'],
                icon=folium.Icon(color='purple')
            ).add_to(m)

    # Mostrar el mapa en Streamlit
    st.write("Consulta la calidad del aire por fecha:")
    fecha_input = st.text_input("Escribe una fecha (YYYY-MM-DD):")

    if fecha_input:
        try:
            fecha_filtrada = pd.to_datetime(fecha_input, format='%Y-%m-%d', errors='raise')
            calidad_filtrada = calidad_df[calidad_df['Fecha'] == fecha_filtrada]
            if not calidad_filtrada.empty:
                st.write("Datos de calidad del aire para la fecha seleccionada:")
                st.dataframe(calidad_filtrada.iloc[:, 1:])  # Muestra todas las columnas excepto la primera
            else:
                st.write("No se encontraron datos para la fecha seleccionada.")
        except ValueError:
            st.write("Por favor, introduce una fecha válida en el formato YYYY-MM-DD.")
    st.write("Los valores de calidad del aire para contaminantes comunes como el dióxido de azufre (SO₂), las partículas finas (PM2.5), el dióxido de nitrógeno (NO₂) y el ozono (O₃) se miden en microgramos por metro cúbico (µg/m³).")
    st.write("Dióxido de Azufre (SO₂): Media de 24 horas: No debe exceder los 20 µg/m³. Media de 10 minutos: No debe exceder los 500 µg/m³.")
    st.write("Partículas Finas (PM2.5): Media anual: No debe exceder los 5 µg/m³. Media de 24 horas: No debe exceder los 15 µg/m³.")
    st.write("Dióxido de Nitrógeno (NO₂): Media anual: No debe exceder los 10 µg/m³. Media de 1 hora: No debe exceder los 200 µg/m³.")
    st.write("Ozono (O₃): Media de 8 horas: No debe exceder los 100 µg/m³.")
    # Mostrar el mapa en Streamlit
    st_folium(m, width=1400, height=700)

# Pestaña de Personas con Discapacidad
with tab4:
    st.title("Ayuda a personas con Discapacidad")
    st.write("En Valencia, las personas con discapacidades también tienen muchas opciones para disfrutar de una buena calidad de vida. La ciudad se ha comprometido a ser inclusiva y accesible, ofreciendo una amplia gama de servicios y actividades adaptadas. Desde transporte público accesible hasta espacios recreativos y culturales diseñados para todos, Valencia asegura que cada uno de sus residentes pueda aprovechar al máximo lo que la ciudad tiene para ofrecer.")
    st.subheader("Localización centros de ayuda")
    st.write("En este apartado hemos implementado un mapa con la localización de todos los diferentes centros de ayuda para discapacitados. Al hacer \"click\" en el icono podrás ver de que centro se trata y su número de teléfono.")

    # Cargar la base de datos de centros de ayuda para discapacitados
    discapacitados_df = pd.read_csv('discapacitados.csv')

    # Crear el mapa
    m = folium.Map(location=[discapacitados_df['Latitud'].mean(), discapacitados_df['Longitud'].mean()], zoom_start=12)

    # Añadir puntos al mapa
    for _, row in discapacitados_df.iterrows():
        lat = row['Latitud']
        lon = row['Longitud']
        nombre = row['equipamien']
        telefono = row['telefono']

        popup_content = f"""
        <div style="font-size: 14px;">
            <b>{nombre}</b><br>
            <i>Teléfono:</i> {telefono}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

    # Checkbox para mostrar aparcamientos
    st.subheader("Aparcamientos movilidad reducida")
    st.write("Somos conscientes de lo complicado que puede ser para una persona que utiliza silla de ruedas poder aparcar y salir de su coche de forma cómoda, es por ello que hemos añadido este botón con el que se puede mostrar en el mapa todos los aparcamientos para personas con mobilidad reducida.")
    show_parking = st.checkbox("Aparcamiento movilidad reducida")
    if show_parking:
        aparcamiento_df = pd.read_csv('aparcamientos.csv')
        for _, row in aparcamiento_df.iterrows():
            lat = row['Latitud']
            lon = row['Longitud']
            plazas = row['plazas']

            popup_content = f"""
            <div style="font-size: 14px;">
                <b>Plazas disponibles:</b> {plazas}
            </div>
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=250),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

    # Mostrar el mapa en Streamlit
    st_folium(m, width=1400, height=700)
