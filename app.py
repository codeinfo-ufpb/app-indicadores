# bash: streamlit run dash/app_tcu.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import locale
from millify import millify
locale.setlocale(locale.LC_ALL, 'pt_BR')

# Customizar a aba da janela do APP
st.set_page_config(page_icon='dash/img/favicon.png', 
                   page_title='Indicadores de Gestão', layout='wide')

# Cabeçalho do App
a,b = st.columns(2)
with a:
    st.image('dash/img/logo-igt.png')
    
with st.expander('⛮ O que são os indicadores do TCU?'):
    st.markdown("""
                Os indicadores de gestão do TCU para universidades objetivam avaliar o desempenho das IFES, 
                estabelecidos nos termos da Decisão TCU nº 408/2002. 
                
                Esses indicadores visam garantir a transparência, a eficiência e a qualidade dos serviços 
                prestados pelas universidades, além de auxiliar na tomada de decisões estratégicas.
                
                Os dados utilizados neste relatório são oriundos do Sistema Integrado de Monitoramento do Ministério da Educação - [SIMEC](https://simec.mec.gov.br)
                
                [Manual dos indicadores](https://shorturl.at/EFFdb)
                """)

col1, col2 = st.columns(2)
with col1:
    with st.expander('☉ Componentes'):
        st.markdown("""
                1. Total de alunos efetivamente matriculados na graduação
                1. Total de alunos efetivamente matriculados na pós-graduação stricto sensu (mestrado e doutorado)
                1. Total de alunos efetivamente matriculados na residência médica
                1. Número de alunos da graduação em tempo integral
                1. Aluno equivalente de graduação
                1. Número de alunos Tempo Integral de pós-graduação
                1. Número de alunos de residência médica
                1. Custo corrente incluindo 35% das despesas HU
                1. Custo corrente excluindo as despesas HU
                1. Número de alunos tempo integral
                1. Número de alunos equivalentes
                1. Número de professores equivalentes
                1. Número de funcionários equivalentes incluindo aqueles a serviço HU
                1. Número de funcionários equivalentes excluindo aqueles a serviço HU
                """)
with col2:
    with st.expander('☉ Indicadores'):
        st.markdown("""
                1. Custo corrente / aluno equivalente tempo integral (incluindo os 35% das despesas HU)
                1. Custo corrente / aluno equivalente tempo integral (excluindo as despesas HU)
                1. Aluno tempo integral / número de professores equivalentes
                1. Aluno tempo integral / número de funcionários equivalentes (incluindo funcionários a serviço HU)
                1. Aluno tempo integral / número de funcionários equivalentes (excluindo funcionários a serviço HU)
                1. Funcionário equivalente / número de professores equivalentes (incluindo funcionários a serviço HU)
                1. Funcionário equivalente / número de professores equivalentes (excluindo funcionários a serviço HU) 
                1. Grau de Participação Estudantil (GPE)
                1. Grau de Envolvimento com Pós-Graduação (GEPG)
                1. Conceito CAPES
                1. Índice de Qualificação do Corpo Docente (IQCD)
                1. Taxa de Sucesso na Graduação (TSG) em %
                """)
        
# # Cache
# st.cache_data.clear() 
@st.cache_data
def load_data():
    p = pd.read_pickle('dash/data/precos.pkl').query('mes==12')[['ano', 'ipca', 'igp', 'igpm']]
    for x in ['ipca', 'igp', 'igpm']:
        p[x] = p[x]/float(p[x].iloc[-1])

    df = (pd.read_pickle('dash/data/tcu.pkl', compression="gzip")
          .assign(rank = lambda x: x.groupby(['codigo', 'ano']).valor
                  .transform(lambda y: y.rank(method='min', ascending=False)).astype(int),
                  rank_m = lambda x: x.groupby(['codigo', 'ano'])['rank'].transform('max'),
                  lrank = lambda x: x['rank'].astype(str)+'/'+x['rank_m'].astype(str)))
    
    return df, p

df, precos = load_data()
d = df.merge(precos, how='left', on='ano').assign(
    variacao = lambda x: x.groupby(['sg_ies', 'codigo'])['valor'].transform('pct_change'))

# # Dimensões
list_tipo = d['tipo'].unique()
list_ies = d.query('sg_ies!="UFPB"').sort_values('sg_ies')['sg_ies'].unique()

with st.sidebar:
    st.image('dash/img/logo-codeinfo.png')
    st.markdown("""---""") 
    st.markdown("""✇ ajustes""")
    uvalor = st.toggle('Correção Monetária', help=f"IPCA (período base: dez/{d.ano.max()})")
    if uvalor:
        uni = st.selectbox('Índice de Preço', ['IPCA', 'IGP', 'IGPM'])
        d = (d.assign(valor = lambda x: np.where(x.descricao.str.contains('Custo'), 
                                                 x.valor/x[uni.lower()], x.valor)))
    
    utipo = st.selectbox('Tipo', ['Indicadores', 'Componentes'])
    upeer = st.selectbox('Benchmark', ['Histórico', 'Brasil', 'Nordeste', 'Similares'], index=1)
    
    st.markdown("""---""")
    st.markdown("© 2024 UFPB | Proplan")

# Aplicação de filtros
if utipo is not None:
    d = d[d.tipo==utipo]
    
print(d)

a,b = st.columns(2) 
with a:
    uano = st.slider('Exercício de Referência', 2015, d.ano.max(), d.ano.max())

lvars = d.sort_values('descricao').descricao.unique()
with b:
    uind = st.multiselect('Variável', lvars, placeholder='Selecione indicadores específicos')
    if len(uind)>0:
        d = d[d.descricao.isin(uind)]
            
with st.expander(f'{utipo} da UFPB no ano de {uano}', True):
        
    r = d.query('sg_ies=="UFPB" and ano==@uano')[['codigo','descricao','lrank','valor','variacao']]
    r=r.rename(columns={'codigo':'Código', 'descricao':'Descrição', 'lrank':'Rank', 'valor':'Valor'})
    vmin, vmax = r.variacao.min(), r.variacao.max()
    r.sort_values('variacao', inplace=True)
    st.dataframe(r.style.format(thousands='.', decimal=',', precision=2), hide_index=True, use_container_width=True,
                 column_config={
                     'variacao': st.column_config.ProgressColumn("Variação", width='small', min_value=vmin, max_value=vmax),
                 })
    
    lvars = d.sort_values('descricao').descricao.unique()
    uind = st.selectbox('Indicador', lvars)
    r = d.query('sg_ies=="UFPB" and descricao==@uind')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = float(r.variacao.tail(1).iloc[0])
        delta = f'{delta*100:.1f}%'
        v = f'{float(r.valor.tail(1).iloc[0]): .2f}'
        st.metric('Último', millify(r.valor.tail(1), precision=2), delta=delta)
    with col2:
        st.metric('Média', millify(r.valor.mean(), precision=2))
    with col3:
        st.metric('Mínimo', millify(r.valor.min(), precision=2))
    with col4:
        st.metric('Máximo', millify(r.valor.max(), precision=2))
    
    fig = px.line(r, x='ano', y='valor', color='codigo', hover_data=['variavel'], markers=True, 
                  color_discrete_map={"variable": "blue", "Gold": "green"})
    fig.add_vline(x=2014, line_width=1, line_dash="dash", line_color="gray")
    fig.add_vline(x=2019, line_width=1, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

# Tab2 - Benchmark
with st.expander(f'{utipo} da UFPB x Benchmark no ano de {uano}', True):
    peers = ["UFC", "UFPE", "UFRN"]
    if upeer=="Similares":
        peers = st.multiselect('IFES', list_ies, ["UFC", "UFPE", "UFRN"])
        if len(peers)==0:
            st.warning(':o: Selecione ao menos uma IFES como benchmark!')
            
    c0 = d.query('sg_ies=="UFPB"')[['ano', 'codigo', 'tipo', 'descricao', 'rank', 'lrank','valor','variacao']]
    c1 = d.query('sg_ies=="UFPB"').groupby(['codigo'], dropna=False)['valor'].median().reset_index()
    c2 = d.query('regiao=="Nordeste"').groupby(['ano','codigo'], dropna=False)['valor'].median().reset_index()
    c3 = d.groupby(['ano','codigo'], dropna=False)['valor'].median().reset_index()
    c4 = d.query('sg_ies.isin(@peers)').groupby(['ano','codigo'], dropna=False)['valor'].mean().reset_index()

    d = (
        c0
        .merge(c1, how='left', on='codigo', suffixes=['','_hi'])
        .merge(c2, how='left', on=['ano','codigo'], suffixes=['','_ne'])
        .merge(c3, how='left', on=['ano','codigo'], suffixes=['','_br'])
        .merge(c4, how='left', on=['ano','codigo'], suffixes=['','_ps'])
        .assign(ihi = lambda x: x['valor']/x['valor_hi'] - 1,
                ine = lambda x: x['valor']/x['valor_ne'] - 1,
                ibr = lambda x: x['valor']/x['valor_br'] - 1,
                ips = lambda x: x['valor']/x['valor_ps'] - 1)
    )
    opcoes={'Histórico': 'hi', 'Brasil': 'br', 'Nordeste': 'ne', 'Similares': 'ps'}
    vcod = opcoes[upeer]

    r = d.query('ano==@uano')[['codigo','descricao','lrank','valor', f'valor_{vcod}', f'i{vcod}']]
    r=r.rename(columns={'codigo':'Código', 'descricao':'Descrição', 'lrank':'Rank', 'valor':'UFPB',
                        f'valor_{vcod}': upeer})
    r.sort_values(f'i{vcod}', inplace=True)
    vmin, vmax = r[f'i{vcod}'].min(), r[f'i{vcod}'].max()
    st.dataframe(r.style.format(thousands='.', decimal=',', precision=2), hide_index=True, use_container_width=True,
                 column_config={
                     f'i{vcod}': st.column_config.ProgressColumn("Diferença", width='small', min_value=vmin, max_value=vmax),
                 })
    
    lvars = d.sort_values('descricao').descricao.unique()
    uind = st.selectbox('Indicador ', lvars)
    r = d.query('descricao==@uind')[['ano','descricao','valor', f'valor_{vcod}']]
    r.rename(columns={'valor':'UFPB', f'valor_{vcod}': upeer}, inplace=True)
    r = r.melt(id_vars=['ano', 'descricao'])
    fig = px.line(r, x='ano', y='value', color='variable', markers=True, color_discrete_map={"variable": "blue", "Gold": "green"})
    fig.add_vline(x=2014, line_width=1, line_dash="dash", line_color="gray")
    fig.add_vline(x=2019, line_width=1, line_dash="dash", line_color="gray")
    # fig = px.bar(r, x='ano', y='value', color='variable', barmode="group", color_discrete_map={"variable": "blue", "Gold": "green"})
    st.plotly_chart(fig, use_container_width=True)
