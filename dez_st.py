import pandas as pd
import streamlit as st
import plotly.express as px

pd.set_option('display.max_colwidth', None)

# (A) Converter a coluna 'DATA / HORA INICIAL' para datetime
# Ajuste o 'format' conforme o padrão do seu Excel (dia/mês ou mês/dia).
fails = pd.read_excel('dez/Planilha de Registros de Falhas Linhares 2024.xlsx', skiprows=1).dropna()
fails['DATA / HORA INICIAL'] = pd.to_datetime(
    fails['DATA / HORA INICIAL'],
    format='%d/%m/%Y %H:%M:%S',  # Ajuste o formato conforme sua necessidade
    errors='coerce'
)

df_lorm_pha = pd.read_csv('dez/dez_events_PHA.txt')
df_lorm_phb = pd.read_csv('dez/dez_events_PHB.txt')

df_lorm_gen_1a10 = pd.read_csv('dez/dez_UG1a10.csv')
df_lorm_gen_11a12 = pd.read_csv('dez/dez_UG11a12.csv')
df_lorm_gen_13a22 = pd.read_csv('dez/dez_UG13a22.csv')
df_lorm_gen_23a24 = pd.read_csv('dez/dez_UG23a24.csv')

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

gen = [genset for genset in lorm_general_events_df['Alarm Group'].unique() if genset.startswith('Gen')]
gen = sorted(gen, key=lambda x: int(x.split('_')[1]))
tags_ugs = [col for col in lorm_generation_df.columns if col != 'DateTime']
tag_to_genset = dict(zip(tags_ugs, gen))

def chart_ug1(df, column_name):
    fig = px.line(df, x='DateTime', y=column_name, title=f'Geração - {column_name}')
    st.plotly_chart(fig, use_container_width=True)

def events_list(df_events):
    st.dataframe(df_events, use_container_width=True)

def filters_results(description_counts, filter_fails):
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        st.dataframe(description_counts, use_container_width=True)
    with col2:
        st.dataframe(filter_fails, use_container_width=True)

def main_layout():
    st.set_page_config(
        page_title="Geração LORM",
        page_icon="⚡️",
        layout="wide"
    )
    st.title('Geração')

    # Cria um seletor de colunas
    selected_tag_ug = st.multiselect("Selecione a TAG da UG para visualizar:", tags_ugs)
    selected_gensets = [tag_to_genset[col] for col in selected_tag_ug]

    # Filtra o DataFrame para a coluna selecionada e intervalo de datas desejado
    df_filtered = lorm_generation_df[['DateTime'] + selected_tag_ug].dropna()

    unique_days = sorted(df_filtered['DateTime'].dt.date.unique())

    start_day = st.selectbox('Data inicial:', unique_days, index=0)
    end_day = st.selectbox('Data final:', unique_days, index=len(unique_days) - 1)

    if end_day < start_day:
        st.warning('A data final deve ser posterior à data inicial.')
        start_day, end_day = end_day, start_day

    # Filtro de datas (dia) para o df de geração
    df_filtered = df_filtered[
        (df_filtered['DateTime'].dt.date >= start_day) &
        (df_filtered['DateTime'].dt.date <= end_day)
    ]

    # Filtro de datas (dia) para os eventos
    df_filt_events = lorm_general_events_df[
        lorm_general_events_df['Alarm Group'].isin(selected_gensets)
    ]
    df_filt_events = df_filt_events[
        (df_filt_events['DateTime'].dt.date >= start_day) &
        (df_filt_events['DateTime'].dt.date <= end_day)
    ]

    # (B) Cria uma cópia de fails para filtrar
    fails_filtered = fails.copy()
    fails_filtered = fails_filtered[
        (fails_filtered['DATA / HORA INICIAL'].dt.date >= start_day) &
        (fails_filtered['DATA / HORA INICIAL'].dt.date <= end_day)
    ]

    # Gera o gráfico com base na coluna selecionada
    chart_ug1(df_filtered, selected_tag_ug)

    st.subheader("Filtros Avançados")
    col_time_1, col_time_2 = st.columns([1, 1])
    start_time_str = col_time_1.text_input("Momento inicial (YYYY-MM-DD HH:MM:SS):", "")
    end_time_str = col_time_2.text_input("Momento final (YYYY-MM-DD HH:MM:SS):", "")

    # Aplica filtro de horário, se informado corretamente
    if start_time_str and end_time_str:
        try:
            start_time = pd.to_datetime(start_time_str, format='%Y-%m-%d %H:%M:%S', errors='raise')
            end_time = pd.to_datetime(end_time_str, format='%Y-%m-%d %H:%M:%S', errors='raise')

            if start_time <= end_time:
                df_filt_events = df_filt_events[
                    (df_filt_events['DateTime'] >= start_time) &
                    (df_filt_events['DateTime'] <= end_time)
                ]
                # (C) Aplica o mesmo filtro em fails_filtered
                fails_filtered = fails_filtered[
                    (fails_filtered['DATA / HORA INICIAL'] >= start_time) &
                    (fails_filtered['DATA / HORA INICIAL'] <= end_time)
                ]
            else:
                st.warning("O momento final deve ser posterior ao momento inicial.")
        except ValueError:
            st.error("Formato de data/hora inválido. Use YYYY-MM-DD HH:MM:SS (Ex: 2024-12-01 14:30:00).")

    # Filtros por colunas: Description, Plant Code, Alarm Group, Alarm State, Value
    colunas_disponiveis = df_filt_events.columns
    col_filter_1, col_filter_2, col_filter_3, col_filter_4, col_filter_5 = st.columns(5)

    desc_filter = col_filter_1.multiselect(
        "Description:",
        options=df_filt_events['Description'].unique() if 'Description' in colunas_disponiveis else [],
        default=[]
    )
    plant_code_filter = col_filter_2.multiselect(
        "Plant Code:",
        options=df_filt_events['Plant Code'].unique() if 'Plant Code' in colunas_disponiveis else [],
        default=[]
    )
    alarm_group_filter = col_filter_3.multiselect(
        "Alarm Group:",
        options=df_filt_events['Alarm Group'].unique() if 'Alarm Group' in colunas_disponiveis else [],
        default=[]
    )
    alarm_state_filter = col_filter_4.multiselect(
        "Alarm State:",
        options=df_filt_events['Alarm State'].unique() if 'Alarm State' in colunas_disponiveis else [],
        default=[]
    )
    value_filter = col_filter_5.multiselect(
        "Value:",
        options=df_filt_events['Value'].unique() if 'Value' in colunas_disponiveis else [],
        default=[]
    )

    if desc_filter:
        df_filt_events = df_filt_events[df_filt_events['Description'].isin(desc_filter)]
    if plant_code_filter and 'Plant Code' in colunas_disponiveis:
        df_filt_events = df_filt_events[df_filt_events['Plant Code'].isin(plant_code_filter)]
    if alarm_group_filter:
        df_filt_events = df_filt_events[df_filt_events['Alarm Group'].isin(alarm_group_filter)]
    if alarm_state_filter and 'Alarm State' in colunas_disponiveis:
        df_filt_events = df_filt_events[df_filt_events['Alarm State'].isin(alarm_state_filter)]
    if value_filter:
        df_filt_events = df_filt_events[df_filt_events['Value'].isin(value_filter)]

    st.subheader("Eventos Após Aplicar Filtros Avançados:")
    events_list(df_filt_events)

    # Cria um dataframe com a contagem de cada descrição após os filtros
    if not df_filt_events.empty:
        description_counts = df_filt_events['Description'].value_counts().reset_index()
        description_counts.columns = ['Description', 'Vezes']
        st.subheader("Contagem dos Eventos e falhas:")
        # Passa fails_filtered ao invés de fails
        filters_results(description_counts, fails_filtered)
    else:
        st.info("Não há eventos para exibir o resumo por Description.")

if __name__ == "__main__":
    main_layout()