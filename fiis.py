import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from datetime import date, timedelta
from bcb import sgs
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import holidays
import feedparser

#Configurar o layout das páginas
st.set_page_config(layout='wide')


def main(): 

    #Função para carregar dados Sidebar
    st.sidebar.title("Menu")
    st.sidebar.markdown("---")
    lista_menu = ["Home", "Dashboard Gerencial","Dashboard Analítico" , "Dashboard Operacional"]
    escolha = st.sidebar.radio("Escolha  a opção", lista_menu)
    carregar_base()
    if escolha == "Home":
        home()
    elif escolha == "Dashboard Gerencial":
        dash_gerencial()
    elif escolha == "Dashboard Analítico":
        dash_analitico()
    elif escolha == "Dashboard Operacional":
        dash_operacional()

def home():
    st.title("Status Report -  Fundos De Investimento Imobiliário (FIIs)")
    #st.write("Fundos de Investimento Imobiliário (FIIs) são uma forma de investimento coletivo em imóveis, permitindo que investidores adquiram cotas de empreendimentos imobiliários e recebam rendimentos mensais.")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("**Atualizado em:** " + str(date.today().strftime('%d/%m/%Y')))
    with col2: st.markdown("**Fonte**: Site da B3, Bacen, Status Invest, Yahoo Finance")
    with col3: st.markdown("**Autor**: Matheus Crepaldi") 

    st.markdown('---')
    
    st.subheader("Introdução")
    st.text('Este dashboard foi desenvolvido como parte do Projeto Aplicado para Pós-Graduação em Ciencia de Dados pela XP Educação.\n Apliquei todas as etapas de ETL (Extração, Transformação e Carregamento dos dados) + Visualização dos Dados, utilizando a linguagem de programação Python.\n Foram longas horas de desenvolvimento e trabalho duro, sou grato a Deus por essa realização e oportunidade e a minha esposa pela paciência')

    
    # Trazer Feed RS do Google, notícias sobre FIIs
    st.title('Principais Notícias Sobre FIIs')


    # URL do feed RSS do Google News para Fundos Imobiliários
    rss_url = "https://news.google.com/rss/search?q=Fundos+Imobiliários&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    # Obter e parsear o feed
    feed = feedparser.parse(rss_url)

    # Criar colunas
    col1, col2 = st.columns(2)

    # Iterar sobre as primeiras notícias e distribuir entre colunas
    for i, entry in enumerate(feed.entries[:6]):  # Pegamos as 10 primeiras notícias
        link_formatado = f"[**{entry.title}**]({entry.link})"

        if i % 2 == 0:
            col1.markdown(link_formatado, unsafe_allow_html=True)
        else:
            col2.markdown(link_formatado, unsafe_allow_html=True)

def carregar_base():
    """Função para carregar a Base_Unificada uma única vez"""
    if "base_unificada" not in st.session_state:
        st.session_state.base_unificada = pd.read_excel("Base_unificada.xlsx")

def dash_gerencial():
    st.title("Dashboard Gerencial")

    with st.spinner('Carregando dados do IFIX...'):
        base_unificada = st.session_state.base_unificada  # Acessando a base carregada


        st.write("Este dashboard apresenta uma visão geral do mercado de Fundos de Investimento Imobiliário (FIIs), incluindo análise dos principais indicadores de mercado.")

        # Definir códigos dos índices no SGS do BCB
        indices = {
            "INCC": 7456,
            "IGP-M": 189,
            "IPCA": 433,
            "Selic": 432,
            "CDI": 12,
            "Inadinplencia": 20617    
            }
     
        # Criar lista de feriados nacionais do Brasil
        feriados_br = holidays.Brazil(years=range(date.today().year - 2, date.today().year + 1))
        # Função para encontrar o último dia útil a partir de uma data
        def ultimo_dia_util(data):
            while data.weekday() >= 5 or data in feriados_br:  # 5 = sábado, 6 = domingo
                data -= timedelta(days=1)
            return data

        # Encontrar a data inicial ajustada (último dia útil dentro de 360 dias)
        data_inicio = ultimo_dia_util(date.today() - timedelta(days=360))
        
        # Obter os dados dos índices
        dados = {indice: sgs.get(codigo, start=data_inicio.isoformat()) for indice, codigo in indices.items()}


        # Criar o DataFrame com informações dos índices
        df_info = pd.DataFrame({'Índice': indices.keys(), 'Código_bcb': indices.values()})

    valores_atuais = []
    valores_anteriores = []
    variacao = []

    for indice, df in dados.items():
        if not df.empty and len(df) > 1:  # Verifica se há pelo menos duas linhas
            valores_atuais.append(df.iloc[-1, 0])  # Última linha
            valores_anteriores.append(df.iloc[-2, 0])  # Penúltima linha
            variacao.append(((df.iloc[-1, 0] / df.iloc[-2, 0]) - 1) * 100)  # Variação percentual
        else:
            valores_atuais.append(0)  # Define zero em caso de erro
            valores_anteriores.append(0)
            variacao.append(0)

    # Garantir que o tamanho das listas corresponda ao índice
    if len(valores_atuais) != len(df_info):
        raise ValueError("Erro: O número de valores extraídos não corresponde ao número de índices!")

    # Adicionar valores ao DataFrame
    df_info['Valor_atual'] = valores_atuais
    df_info['Valor_Anterior'] = valores_anteriores
    df_info['Variação (%)'] = variacao

        
    # Apresentação do Dashboard
                
    # Criando a visualização dos índices
    colunas = st.columns(3)

        # Iterando sobre os índices para distribuir nas colunas dinamicamente
    for i, col in enumerate(colunas):
        for j in range(i, len(df_info), 3):  # Distribuindo os índices entre as colunas
            with col:
                st.metric(df_info['Índice'][j], value=df_info['Valor_atual'][j], delta=str(df_info['Variação (%)'][j]) + '%')


    # Grafico de Composição do IFIX por Setor     
    col1, col2 = st.columns(2)
    with col2:
            st.subheader("Percentual IFIX por Setor")
            composicao_ifix = base_unificada[['Setor','Part%']].groupby('Setor').tail(1)  # Obtém a última linha de cada grupo
            # Criando o Treemap com Plotly
            fig = px.treemap(composicao_ifix, 
                            path=['Setor'],  # Agrupar por setor
                            values='Part%',  # Tamanho baseado no percentual
                            color='Setor')  # Cor baseada no setor
            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
        #Gráfico Evolução do IFIX
    with col1:
        st.subheader('Evolução Mensal do IFIX')
        evolucao_ifix = pd.read_csv("Evolucao_Mensal.csv", header = 1, encoding='latin-1',decimal = ',' ,sep = ';')        # Conversão da coluna para float     evolucao_ifix['Valor'] = evolucao_ifix['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        evolucao_ifix = evolucao_ifix.rename(columns={'Ano': 'year', 'Mês': 'month'})                        
        evolucao_ifix['day'] = 1  # Define o dia como 1
        # Agora, converta para datetime
        evolucao_ifix['Data'] = pd.to_datetime(evolucao_ifix[['year', 'month', 'day']])
        evolucao_ifix.drop(columns=['month','year','day'],inplace=True) 
        st.line_chart(evolucao_ifix.set_index('Data')['Valor'],width=200, height=300, use_container_width=True)
                    
def dash_analitico():
    st.title("Dashboard Analítico")

    base_unificada = st.session_state.base_unificada  # Acessando a base carregada

# Raking oportunidades
    ranking = base_unificada.groupby('Ticker').tail(1)
    # Remover separadores de milhar e substituir vírgula por ponto decimal
        # Substituir valores vazios por NaN
    ranking['Liq_Diaria'] = ranking['Liq_Diaria'].replace('', np.nan)
        # Remover espaços em branco extras
    ranking['Liq_Diaria'] = ranking['Liq_Diaria'].str.strip()
        # Remover separadores de milhar e substituir vírgula por ponto decimal
    ranking['Liq_Diaria'] = ranking['Liq_Diaria'].str.replace('.', '', regex=True).str.replace(',', '.', regex=True)
        # Verificar se ainda há valores não numéricos
        # Converter para float
    ranking['Liq_Diaria'] = pd.to_numeric(ranking['Liq_Diaria'], errors='coerce')
     # Substituir NaN por 0 (ou outro valor adequado)
    ranking['Liq_Diaria'].fillna(0, inplace=True)
    

    # 🔹 **Filtros lado a lado**
    col1, col2 = st.columns([1,2])
    with col1:
        objetivo = st.selectbox(
        "**📊Selecione a Tese de Investimentos:**",
        ["Estratégia Geral","Renda passiva", "Valorização Patrimonial"]
        )
    with col2:
        setores_disponiveis = ['All Setores'] + list(ranking['Setor'].unique())
        setor_selecionado = st.selectbox("**🏢 Filtrar por Setor:**", setores_disponiveis)



    pesos_objetivos = {
        "Renda passiva": {'Preço': 0.1, 'Rentabilidade_Normalizada': 0.15, 'DY': 0.4, 'P/PV': 0.1, 'Liq_Diaria': 0.25},
        "Valorização Patrimonial": {'Preço': 0.1, 'Rentabilidade_Normalizada': 0.35, 'DY': 0.1, 'P/PV': 0.3, 'Liq_Diaria': 0.15},
        "Estratégia Geral": {'Preço': 0.1, 'Rentabilidade_Normalizada': 0.25, 'DY': 0.3, 'P/PV': 0.15, 'Liq_Diaria': 0.2}
    }

    # Aplicar os pesos conforme a seleção do usuário
    pesos = pesos_objetivos[objetivo]

    # **Filtrar os dados pelo setor escolhido**

    if setor_selecionado != 'All Setores':
        ranking = ranking[ranking['Setor'] == setor_selecionado]

    
    # 👉 **Normalização das variáveis**
    scaler = MinMaxScaler()
    ranking[['Preço', 'P/PV']] = 1 - scaler.fit_transform(ranking[['Preço', 'P/PV']])
    ranking[['DY', 'Liq_Diaria']] = scaler.fit_transform(ranking[['DY', 'Liq_Diaria']])

    # Calcular pontuação baseada nos pesos escolhidos
    ranking['Ranking'] = ranking[['Preço', 'Rentabilidade_Normalizada', 'DY', 'P/PV', 'Liq_Diaria']].apply(lambda row: sum(row[metric] * pesos[metric] for metric in pesos), axis=1)

    # Ordenar ranking
    ranking = ranking.sort_values(by='Ranking', ascending=False)
    ranking.rename(columns={'Rentabilidade_Normalizada': 'Rent_Acumulada'})
    ranking.index = ranking['Ticker']
    st.subheader(f"🔥 Ranking dos FIIs - {objetivo} - {setor_selecionado}")
    
    # Exibir tabela com ranking atualizado (1-5 posições)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('TOP 10 - Melhores FIIs')
        st.write(ranking[['Setor']].head(10))
        st.markdown('---')

    with col2:
        # Gráfico Rentabilidade Acumulada
        st.write("### 📊 Rentabilidade Acumulada - Último Ano")
            # Aplicar filtro na Base_unificada
        filtro = ranking['Ticker'].head(10).unique()
        base_rent = base_unificada[base_unificada['Ticker'].isin(filtro)]
        base_rent.index = base_rent['Data']
        base_rent.drop(columns=['Data'], inplace=True)
        base_rent = base_rent[['Setor','Ticker','Rentabilidade_Normalizada']]

            # Criar gráfico de linhas com Plotly
        fig = px.line(base_rent, x=base_rent.index, y=base_rent['Rentabilidade_Normalizada'], color=base_rent['Ticker'], subtitle="📈 Rentabilidade dos FIIs ao longo do tempo")

            # Exibir gráfico no Streamlit
        st.plotly_chart(fig)

def dash_operacional():
    st.title("Dashboard Operacional")
    base_unificada = st.session_state.base_unificada  # Acessando a base carregada

    filtro = base_unificada[['Ticker', 'Setor']].groupby('Ticker').tail(1)
    # Filtrar as ações com base no setor escolhido

    # Criar colunas para organizar filtros lado a lado
    col1, col2 = st.columns(2)

    with col1:
        setores_disponiveis = ['Indiferente'] + list(filtro['Setor'].unique())
        setor_selecionado = st.selectbox("🏢 Filtrar por Setor:", setores_disponiveis)

    with col2:
        if setor_selecionado == "Indiferente":
            tickers_disponiveis = list(filtro['Ticker'].unique())  # Todos os tickers
        else:
            tickers_disponiveis = list(filtro[filtro['Setor'] == setor_selecionado]['Ticker'].unique())

        ticker_selecionado = st.selectbox("📈 Filtrar por Ticker:", tickers_disponiveis)

    st.markdown('---')
    # Gráfico de Linha do Preço com Média Móvel
    preco= yf.download(ticker_selecionado + '.SA', period="2y")  # Obtendo o preço de fechamento
    preco.columns = preco.columns.get_level_values(0) #Organiza o yf para formato correto
 
    
    preco["MM50"] = preco["Close"].rolling(50).mean()  # Média Móvel de 9 períodos
    preco["MM200"] = preco["Close"].rolling(200).mean()  # Média Móvel de 21 períodos
   

    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=preco.index, y=preco['Close'], mode='lines', name='Preço'))
    fig.add_trace(go.Scatter(x=preco.index, y=preco["MM50"], mode='lines', name='Média Móvel 50'))
    fig.add_trace(go.Scatter(x=preco.index, y=preco["MM200"], mode='lines', name='Média Móvel 200'))
    fig.update_layout(title=f'Gráfico de Preço com Médias Móveis - {ticker_selecionado}',
                  xaxis_title='Data', yaxis_title='Preço')
    st.plotly_chart(fig, use_container_width=True)


    st.markdown('---')

    # Gráfico de Candlestick do Preço Diário
    diario = yf.download(ticker_selecionado + '.SA', period='1d', interval="5m")
    diario.columns = diario.columns.get_level_values(0) #Organiza o yf para formato correto
 
    fig = go.Figure(data=[go.Candlestick(x=diario.index,
                                         open=diario['Open'],
                                         high=diario['High'],
                                         low=diario['Low'],
                                         close=diario['Close'])])
    fig.update_layout(title=f'Gráfico Diário - Candlestick - {ticker_selecionado}', xaxis_rangeslider_visible=False, xaxis_title='Data', yaxis_title='Preço')
    st.plotly_chart(fig, use_container_width=True)  



    # Exibindo os filtros aplicados
    st.write(f"Setor escolhido: **{setor_selecionado}**")
    st.write(f"Ação escolhida: **{ticker_selecionado}**")

main()




