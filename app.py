import streamlit as st
from query_engine import generate_sql_and_analysis, run_query
import matplotlib.pyplot as plt

st.set_page_config(page_title="Asistente Licitaciones IA", layout="wide")
st.title("🤖 Asistente IA para Licitaciones")

q = st.text_input("Escribe tu pregunta sobre licitaciones:")
if q:
    with st.spinner("Generando SQL y análisis…"):
        sql, analysis = generate_sql_and_analysis(q)
    if sql:
        st.subheader("SQL generado:")
        st.code(sql, language="sql")
        df = run_query(sql)
        st.subheader("Resultados:")
        st.dataframe(df)
        # Gráfica si hay al menos 2 columnas
        if df.shape[1] >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
            fig, ax = plt.subplots()
            ax.bar(df[x_col].astype(str), df[y_col])
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
    else:
        st.error("No se pudo extraer la consulta SQL.")
    st.subheader("Análisis de la IA:")
    st.write(analysis)