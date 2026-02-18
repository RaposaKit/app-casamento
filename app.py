import streamlit as st
import gspread
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Lista de Casamento", page_icon="💍", layout="wide")

# Conectar ao Google Sheets
@st.cache_resource
def conectar_planilha():
    try:
        # Tenta conectar usando o arquivo local (para rodar no seu PC)
        gc = gspread.service_account(filename='credenciais.json')
    except FileNotFoundError:
        # Se não achar o arquivo (porque está na nuvem), pega a senha dos Segredos do Streamlit
        credenciais = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credenciais)
        
    planilha = gc.open('Lista_Casamento').sheet1
    return planilha
# Tenta conectar. Se der erro, avisa na tela.
try:
    aba = conectar_planilha()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha. Verifique se o nome está certo e se você compartilhou a planilha com o e-mail do arquivo JSON.")
    st.stop()

st.title("💍 Gerenciador de Lista de Casamento")

# --- Formulário para adicionar pessoas ---
with st.form("cadastro", clear_on_submit=True):
    nome = st.text_input("Nome completo do convidado")
    categoria = st.selectbox("Papel no casamento:", ["Convidado Geral", "Padrinho", "Madrinha"])
    botao = st.form_submit_button("Adicionar à Lista")

    if botao and nome:
        # Adiciona uma nova linha na planilha do Google
        aba.append_row([nome, categoria])
        st.success(f"{nome} foi salvo na planilha com sucesso!")

st.divider()

# --- Exibir os Dados atualizados ---
dados = aba.get_all_records()

if dados:
    df = pd.DataFrame(dados)
    
    # TRATAMENTO DE ERRO: Verifica se as colunas existem antes de tentar separar
    if 'Categoria' not in df.columns or 'Nome' not in df.columns:
        st.warning("⚠️ Ops! Parece que os títulos 'Nome' ou 'Categoria' sumiram da Linha 1 da sua planilha. Por favor, recoloque-os para a tabela voltar a funcionar.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎩 Padrinhos e Madrinhas")
            vips = df[df['Categoria'].isin(['Padrinho', 'Madrinha'])]
            st.dataframe(vips, hide_index=True, use_container_width=True)
            st.caption(f"Total: {len(vips)} pessoas")

        with col2:
            st.subheader("🎉 Convidados em Geral")
            gerais = df[df['Categoria'] == 'Convidado Geral']
            st.dataframe(gerais, hide_index=True, use_container_width=True)
            st.caption(f"Total: {len(gerais)} pessoas")
else:
    st.info("A lista ainda está vazia. Adicione o primeiro convidado acima!")