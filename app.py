import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#appTotal

# Configuración de la página
st.set_page_config(page_title="Dashboard Actigraph - MMASH", page_icon="📊", layout="wide")

st.title("📊 Panel de Análisis Actigraph (MMASH)")
st.markdown("Exploración interactiva de los datos biométricos de los 22 usuarios.")

# Carga de datos optimizada con caché
@st.cache_data
def load_data():
    df = pd.read_csv('Actigraph.csv')
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Visualización")
usuarios_disponibles = sorted(df['user'].unique())
usuario_seleccionado = st.sidebar.selectbox("Selecciona un usuario", ["Todos"] + usuarios_disponibles)

# Filtrar dataframe según selección
if usuario_seleccionado != "Todos":
    df_filtered = df[df['user'] == usuario_seleccionado]
else:
    df_filtered = df

# --- MÉTRICAS PRINCIPALES ---
st.subheader(f"Resumen para: {usuario_seleccionado}")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Registros Totales", f"{len(df_filtered):,}")
with col2:
    st.metric("Pasos Totales", f"{int(df_filtered['Steps'].sum()):,}")
with col3:
    st.metric("Frecuencia Cardíaca Media", f"{df_filtered['HR'].mean():.1f} bpm")
with col4:
    st.metric("HR Máxima", f"{df_filtered['HR'].max():.0f} bpm")

st.divider()

# --- SECCIÓN DE GRÁFICOS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Distribución de Frecuencia Cardíaca (HR)")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df_filtered['HR'], bins=30, kde=True, color='crimson', ax=ax)
    ax.set_title("Histograma de HR")
    ax.set_xlabel("BPM")
    ax.set_ylabel("Frecuencia")
    st.pyplot(fig)

with col_g2:
    st.subheader("Proporción de Posturas (Inclinómetro)")
    # Calcular porcentajes de posturas
    posturas = {
        'De Pie': df_filtered['Inclinometer Standing'].sum(),
        'Sentado': df_filtered['Inclinometer Sitting'].sum(),
        'Acostado': df_filtered['Inclinometer Lying'].sum(),
        'Apagado/Off': df_filtered['Inclinometer Off'].sum()
    }
    df_posturas = pd.DataFrame(list(posturas.items()), columns=['Postura', 'Conteo'])
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.pie(df_posturas['Conteo'], labels=df_posturas['Postura'], autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
    ax.axis('equal')
    st.pyplot(fig)

# --- TABLA DE DATOS CRUDOS ---
with st.expander("Ver datos detallados"):
    st.dataframe(df_filtered.head(100))
