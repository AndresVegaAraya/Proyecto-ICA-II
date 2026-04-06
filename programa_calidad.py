import streamlit as st
import pandas as pd

st.set_page_config(page_title="Homologador y Visor", layout="wide")

st.title("🔄 Homologador y Visualizador de Datos")
st.markdown("Sube tu archivo de Excel, limpia tus datos en la primera pestaña y analízalos en la segunda.")

# 1. Subir el archivo (esto se queda fuera de las pestañas para que aplique a ambas)
archivo_subido = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # 2. Guardar el DataFrame en la memoria de la sesión y reiniciar variables
    if "nombre_archivo" not in st.session_state or st.session_state.nombre_archivo != archivo_subido.name:
        # Cargamos los nuevos datos
        st.session_state.df = pd.read_excel(archivo_subido, engine='openpyxl')
        st.session_state.nombre_archivo = archivo_subido.name
        
        # ¡AQUÍ ESTÁ LA CLAVE! 
        # Si el archivo es nuevo, el historial debe empezar desde cero obligatoriamente.
        st.session_state.historial = []
    
    # Asignamos el df guardado a una variable para usarlo más fácil
    df = st.session_state.df
    
    # Mantenemos esta validación por seguridad (por si en alguna otra parte del código 
    # se llega a borrar la variable historial por accidente)
    if "historial" not in st.session_state:
        st.session_state.historial = []

    # --- CREACIÓN DE PESTAÑAS ---
    tab1, tab2 = st.tabs(["🔄 Homologación de Datos", "📊 Visualización de Gráficos"])
    
    # ==========================================
    # PESTAÑA 1: HOMOLOGACIÓN
    # ==========================================
    with tab1:
        st.subheader("1. Vista previa de los datos")
        st.dataframe(df.head(), use_container_width=True)
        st.divider()
        
        st.subheader("2. Configura la homologación")
        columna_seleccionada = st.selectbox("Elige la columna a homologar:", df.columns, key="col_homologar")
        
        if columna_seleccionada:
            valores_unicos = df[columna_seleccionada].dropna().unique().tolist()
            
            valores_a_cambiar = st.multiselect(
                f"Selecciona los valores de '{columna_seleccionada}' que quieres modificar:",
                options=valores_unicos
            )
            
            if valores_a_cambiar:
                opciones_destino = ["-- Escribir manualmente --"] + valores_unicos
                valor_destino_seleccionado = st.selectbox("Selecciona el valor final homologado:", options=opciones_destino)
                
                if valor_destino_seleccionado == "-- Escribir manualmente --":
                    nuevo_valor = st.text_input("Escribe el nuevo valor:")
                else:
                    nuevo_valor = valor_destino_seleccionado
                
                if st.button("Aplicar Homologación", type="primary"):
                    if nuevo_valor:
                        # 1. Aplicamos el cambio
                        df[columna_seleccionada] = df[columna_seleccionada].replace(valores_a_cambiar, nuevo_valor)
                        st.session_state.df = df
                        
                        # 2. NUEVO: Guardamos el registro en el historial
                        registro = f"✅ Columna '{columna_seleccionada}': Se cambió {valores_a_cambiar} por '{nuevo_valor}'"
                        st.session_state.historial.append(registro)
                        
                        st.success("¡Valores actualizados!")
                        st.rerun()
            
            # --- SECCIÓN DE TRAZABILIDAD --
            st.divider()
            with st.expander("📜 Ver Historial de Cambios (Trazabilidad)"):
                if st.session_state.historial:
                    # Mostramos cada registro en formato de lista
                    for item in st.session_state.historial:
                        st.write(item)
                    
                    # Botón opcional para limpiar el historial si se desea empezar de cero
                    if st.button("Limpiar Historial"):
                        st.session_state.historial = []
                        st.rerun()
                else:
                    st.info("Aún no se han realizado homologaciones en esta sesión.")
            
            st.divider()
            
            st.subheader("3. Resultado Final y Descarga")
            
            # --- NUEVO: Herramienta de filtrado para verificación ---
            st.write("🔍 **Verifica tus datos:** Aplica filtros para comprobar que la homologación se realizó correctamente.")
            
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                # El index predeterminado será la columna que el usuario está homologando actualmente
                idx_col = list(st.session_state.df.columns).index(columna_seleccionada) if columna_seleccionada in st.session_state.df.columns else 0
                columna_filtro = st.selectbox("Filtrar por columna:", st.session_state.df.columns, index=idx_col, key="col_filtro")
                
            with col_f2:
                valores_unicos_filtro = st.session_state.df[columna_filtro].dropna().unique().tolist()
                valores_seleccionados = st.multiselect(
                    "Mostrar solo estos valores (deja vacío para ver todos):", 
                    options=valores_unicos_filtro, 
                    key="val_filtro"
                )
            
            # Lógica de filtrado de Pandas
            if valores_seleccionados:
                # Filtramos: Nos quedamos solo con las filas donde el valor esté en la lista seleccionada
                df_final = st.session_state.df[st.session_state.df[columna_filtro].isin(valores_seleccionados)]
            else:
                # Si no hay filtros, mostramos la tabla completa
                df_final = st.session_state.df
                
            # Mostramos el DataFrame (ya sea el completo o el filtrado)
            st.dataframe(df_final, use_container_width=True)
            
            # Un pequeño texto útil para saber cuántas filas estamos viendo
            st.caption(f"Mostrando {len(df_final)} filas de un total de {len(st.session_state.df)}.")
            
            # --- SECCIÓN DE DESCARGA ---
            # El CSV ahora exportará df 
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos (CSV)",
                data=csv,
                file_name='datos_homologados.csv',
                mime='text/csv',
            )

    # ==========================================
    # PESTAÑA 2: VISUALIZACIÓN
    # ==========================================
    with tab2:
        st.subheader("📊 Análisis de Columnas")
        st.write("Selecciona una columna principal y, opcionalmente, una segunda para desagregar los datos.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            col_principal = st.selectbox("Eje X (Columna principal):", df.columns, key="col_principal")
            
        with col2:
            opciones_desglose = ["-- Ninguno --"] + list(df.columns)
            col_desglose = st.selectbox("Color (Desagregar por):", opciones_desglose, key="col_desglose")
        
        # --- NUEVO: Control para elegir el Top N ---
        st.write("---") # Línea separadora visual
        top_n = st.slider("Cantidad de barras a mostrar (Top N):", min_value=1, max_value=20, value=5)
        
        if col_principal:
            if col_desglose == "-- Ninguno --":
                # 1. Gráfico simple (Top N)
                # value_counts() ya ordena de mayor a menor por defecto, solo cortamos con head()
                conteo_datos = df[col_principal].value_counts().head(top_n)
                
                st.bar_chart(conteo_datos)
                
                with st.expander("Ver tabla de frecuencias"):
                    st.dataframe(conteo_datos.reset_index().rename(columns={col_principal: 'Valor', 'count': 'Frecuencia'}), use_container_width=True)
            
            else:
                # 2. Gráfico apilado (Top N)
                tabla_cruzada = pd.crosstab(df[col_principal], df[col_desglose])
                
                # Para saber cuáles son los "Top N", sumamos los totales de cada fila (axis=1)
                totales_por_fila = tabla_cruzada.sum(axis=1)
                
                # Ordenamos esos totales de mayor a menor y extraemos los nombres de las 5 categorías principales
                top_categorias = totales_por_fila.sort_values(ascending=False).head(top_n).index
                
                # Filtramos la tabla cruzada original para quedarnos solo con esas filas ganadoras
                tabla_cruzada_top = tabla_cruzada.loc[top_categorias]
                
                st.bar_chart(tabla_cruzada_top)
                
                with st.expander("Ver tabla de datos cruzados"):
                    st.dataframe(tabla_cruzada_top, use_container_width=True)