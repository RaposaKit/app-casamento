import streamlit as st
import gspread
import pandas as pd

st.set_page_config(page_title="Lista de Casamento", page_icon="💍", layout="wide")

# Conectar ao Google Sheets
@st.cache_resource
def conectar_planilha():
    try:
        gc = gspread.service_account(filename='credenciais.json')
    except FileNotFoundError:
        credenciais = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credenciais)
    return gc.open('Lista_Casamento').sheet1

try:
    aba = conectar_planilha()
except Exception as e:
    st.error("Erro ao conectar com a planilha.")
    st.stop()

st.title("💍 Gerenciador de Lista de Casamento")

# --- Novo Formulário ---
with st.form("cadastro", clear_on_submit=True):
    st.subheader("Adicionar Novo Convite")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome do titular do convite")
        # AQUI VOCÊ ADICIONA AS CATEGORIAS ESPECÍFICAS:
        categoria = st.selectbox(
            "Grupo/Categoria:", 
            ["Padrinho", "Madrinha", "Família da Noiva", "Família do Noivo", "Amigos de Infância", "Amigos do Trabalho"]
        )
        
    with col2:
        acompanhantes = st.number_input("Quantidade de acompanhantes extras", min_value=0, max_value=10, value=0)
        confirmado = st.selectbox("Status de Presença:", ["Pendente", "Sim", "Não"])
        
    botao = st.form_submit_button("Salvar Convite")

    if botao and nome:
        # Salva exatamente na ordem: Nome, Categoria, Acompanhantes, Confirmado
        aba.append_row([nome, categoria, acompanhantes, confirmado])
        st.success(f"Convite para {nome} salvo com sucesso!")

st.divider()

# --- Exibir e Baixar os Dados ---
dados = aba.get_all_records()

if dados:
    df = pd.DataFrame(dados)
    
    col_titulo, col_botao = st.columns([3, 1])
    with col_titulo:
        st.subheader("📋 Lista Completa")
    with col_botao:
        # Transformar tabela em CSV para Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Planilha", 
            data=csv, 
            file_name="lista_casamento.csv", 
            mime="text/csv"
        )
    
    # Exibe a tabela completa com as novas colunas
    st.dataframe(df, hide_index=True, use_container_width=True)
    
    # --- Painel de Resumo Matemático ---
    st.divider()
    st.subheader("📊 Resumo do Evento")
    
    total_convites = len(df)
    # Garante que a coluna acompanhantes seja tratada como número para somar
    df['Acompanhantes'] = pd.to_numeric(df['Acompanhantes'], errors='coerce').fillna(0)
    total_acompanhantes = int(df['Acompanhantes'].sum())
    total_pessoas = total_convites + total_acompanhantes
    
    # Conta quantos disseram "Sim"
    confirmados = df[df['Confirmado'] == 'Sim']
    total_confirmados = len(confirmados) + int(pd.to_numeric(confirmados['Acompanhantes'], errors='coerce').fillna(0).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Convites", total_convites)
    c2.metric("Total de Pessoas (Com acompanhantes)", total_pessoas)
    c3.metric("Presenças Confirmadas (Sim)", total_confirmados)

else:
    st.info("A lista ainda está vazia. Adicione o primeiro convidado!")
