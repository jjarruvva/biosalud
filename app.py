import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Actigraph - MMASH", page_icon="📊", layout="wide")

st.title("📊 Panel de Comparación - Actigraph (MMASH)")
st.markdown("Selecciona múltiples usuarios en la barra lateral para comparar sus patrones biométricos. Todas las gráficas son interactivas.")

# Carga de datos optimizada con caché
@st.cache_data
def load_data():
    df = pd.read_csv('actigraph_1_7.csv')
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Visualización")
usuarios_disponibles = sorted(df['user'].unique())

# Selector múltiple de usuarios
usuarios_seleccionados = st.sidebar.multiselect(
    "Selecciona usuarios a comparar", 
    options=usuarios_disponibles, 
    default=usuarios_disponibles[:2] if len(usuarios_disponibles) >= 2 else usuarios_disponibles
)

if not usuarios_seleccionados:
    st.warning("Por favor, selecciona al menos un usuario en la barra lateral.")
else:
    # Filtrar dataframe según selección múltiple
    df_filtered = df[df['user'].isin(usuarios_seleccionados)]

    # --- TABLA RESUMEN COMPARATIVA ---
    st.subheader("📋 Resumen Comparativo por Usuario")
    resumen_comparativo = df_filtered.groupby('user').agg(
        Registros=('HR', 'count'),
        Pasos_Totales=('Steps', 'sum'),
        HR_Media=('HR', 'mean'),
        HR_Max=('HR', 'max'),
        Sentado_Pct=('Inclinometer Sitting', 'mean'),
        DePie_Pct=('Inclinometer Standing', 'mean'),
        Acostado_Pct=('Inclinometer Lying', 'mean')
    ).reset_index()

    # Convertir a porcentajes las proporciones de posturas
    resumen_comparativo[['Sentado_Pct', 'DePie_Pct', 'Acostado_Pct']] *= 100

    st.dataframe(resumen_comparativo.style.format({
        'Pasos_Totales': '{:,}',
        'HR_Media': '{:.1f} bpm',
        'HR_Max': '{:.0f} bpm',
        'Sentado_Pct': '{:.1f}%',
        'DePie_Pct': '{:.1f}%',
        'Acostado_Pct': '{:.1f}%'
    }), use_container_width=True)

    st.divider()

    # --- SECCIÓN DE GRÁFICOS (1 y 2) ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📈 Distribución de Frecuencia Cardíaca (HR)")
        fig_hist = px.histogram(
            df_filtered, 
            x='HR', 
            color='user', 
            barmode='group',
            histnorm='density',
            nbins=30,
            opacity=0.6,
            labels={'HR': 'Frecuencia Cardíaca (BPM)', 'count': 'Densidad', 'user': 'Usuario'},
            title="Comparativa de Densidad de HR (BPM)"
        )
        fig_hist.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Frecuencia Cardíaca (BPM)",
            yaxis_title="Densidad"
        )

        # Habilitar explícitamente el scrollZoom en la configuración del gráfico en Streamlit
        st.plotly_chart(
            fig_hist, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True}
        )

    with col_g2:
        st.subheader("🚶‍♂️ Comparativa de Pasos Totales")
        pasos_por_usuario = df_filtered.groupby('user')['Steps'].sum().reset_index()
        fig_bar_steps = px.bar(
            pasos_por_usuario, 
            x='user', 
            y='Steps', 
            color='user',
            labels={'user': 'Usuario', 'Steps': 'Pasos Totales'},
            title="Suma Total de Pasos por Usuario"
        )
        fig_bar_steps.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_tickangle=-45
        )

        # Habilitar explícitamente el scrollZoom en la configuración del gráfico en Streamlit
        st.plotly_chart(
            fig_bar_steps, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True}
        )

    st.divider()

    # --- SECCIÓN DE GRÁFICOS (3 y 4) ---
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("🧘‍♂️ Comparativa de Posturas (Tiempo Promedio)")
        posturas_df = df_filtered.groupby('user')[['Inclinometer Standing', 'Inclinometer Sitting', 'Inclinometer Lying', 'Inclinometer Off']].mean().reset_index()
        posturas_melted = posturas_df.melt(id_vars='user', value_vars=['Inclinometer Standing', 'Inclinometer Sitting', 'Inclinometer Lying', 'Inclinometer Off'], var_name='Postura', value_name='Proporción')

        reemplazos = {
            'Inclinometer Standing': 'De Pie',
            'Inclinometer Sitting': 'Sentado',
            'Inclinometer Lying': 'Acostado',
            'Inclinometer Off': 'Off / Apagado'
        }
        posturas_melted['Postura'] = posturas_melted['Postura'].map(reemplazos)
        posturas_melted['Proporción'] *= 100

        fig_post = px.bar(
            posturas_melted, 
            x='user', 
            y='Proporción', 
            color='Postura', 
            barmode='group',
            labels={'user': 'Usuario', 'Proporción': 'Porcentaje del tiempo (%)', 'Postura': 'Postura'},
            title="Proporción de Tiempo por Postura y Usuario"
        )
        fig_post.update_layout(
            margin=dict(l=20, r=20, t=40, b=20)
        )

        # Habilitar explícitamente el scrollZoom en la configuración del gráfico en Streamlit
        st.plotly_chart(
            fig_post, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True}
        )

    with col_g4:
        st.subheader("⏱️ Evolución Temporal de HR (Interactiva)")

        # Preparar datos con índice temporal relativo por usuario
        df_list = []
        for u in usuarios_seleccionados:
            df_u = df_filtered[df_filtered['user'] == u].copy()
            df_u['relative_time'] = range(len(df_u))
            df_list.append(df_u)

        df_time_superposed = pd.concat(df_list)

        # Submuestreo dinámico para garantizar fluidez interactiva
        if len(df_time_superposed) > 15000:
            step_sampling = max(1, len(df_time_superposed) // 8000)
            df_plot_line = df_time_superposed.iloc[::step_sampling]
        else:
            df_plot_line = df_time_superposed

        # Gráfico interactivo con Plotly
        fig_line = px.line(
            df_plot_line, 
            x='relative_time', 
            y='HR', 
            color='user',
            labels={'relative_time': 'Secuencia de Registros (Tiempo Relativo)', 'HR': 'Frecuencia Cardíaca (BPM)'},
            title="Evolución de HR Superpuesta (Usa la rueda del ratón para hacer Zoom)"
        )

        fig_line.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Habilitar explícitamente el scrollZoom en la configuración del gráfico en Streamlit
        st.plotly_chart(
            fig_line, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True}
        )

    # --- VISTA DE DATOS CRUDOS ---
    with st.expander("🔍 Ver datos detallados filtrados"):
        st.dataframe(df_filtered.head(200))
