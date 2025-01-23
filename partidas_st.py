import pandas as pd
import streamlit as st
import plotly.express as px

df_lorm_pha = pd.read_csv('data/2024nov_events_PHA.txt')
df_lorm_phb = pd.read_csv('data/2024nov_events_PHB.txt')

df_lorm_gen_1a10 = pd.read_csv('data/2024nov_UG1a10.csv')
df_lorm_gen_11a12 = pd.read_csv('data/2024_nov_UG11e12.csv')
df_lorm_gen_13a22 = pd.read_csv('data/2024nov_UG13a22.csv')
df_lorm_gen_23a24 = pd.read_csv('data/2024nov_UG23e24.csv')

df_lorm_generation = pd.concat([
    df_lorm_gen_1a10,
    df_lorm_gen_11a12,
    df_lorm_gen_13a22,
    df_lorm_gen_23a24
], ignore_index=True)

df_geral = pd.concat([df_lorm_pha, df_lorm_phb], ignore_index=True)

lorm_general_events_df = df_geral
lorm_generation_df = df_lorm_generation

lorm_general_events_df['DateTime'] = pd.to_datetime(lorm_general_events_df['DateTime'])
lorm_generation_df['DateTime'] = pd.to_datetime(lorm_generation_df['DateTime'])

def chart_ug1(df, column_name):
    fig = px.line(df, x='DateTime', y=column_name, title=f'Valores ao Longo do Tempo - {column_name}')
    st.plotly_chart(fig, use_container_width=True)

def main_layout():
    st.set_page_config(
        page_title="Geração LORM",
        page_icon="⚡️",
        layout="wide"
    )

    st.title('Geração')

    # Lista de colunas disponíveis (excluindo "DateTime")
    available_columns = [col for col in lorm_generation_df.columns if col != 'DateTime']

    # Cria um seletor de colunas
    selected_col = st.selectbox("Selecione a a UG para visualizar os dados de geração:", available_columns)

    # Filtra o DataFrame para a coluna selecionada e intervalo de datas desejado
    df_filtered = lorm_generation_df[['DateTime', selected_col]].dropna()
    df_filtered = df_filtered[(df_filtered['DateTime'].dt.day >= 2) & (df_filtered['DateTime'].dt.day < 23)]

    # Gera o gráfico com base na coluna selecionada
    chart_ug1(df_filtered, selected_col)

if __name__=="__main__":
    main_layout()