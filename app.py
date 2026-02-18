import streamlit as st
import gspread
import pandas as pd

st.set_page_config(page_title="App do Casamento", page_icon="💍", layout="wide")

# Conectar ao Google Sheets
@st.cache_resource
def conectar_planilha():
    try:
        gc = gspread.service_account(filename='credenciais.json')
    except FileNotFoundError:
        credenciais = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credenciais)
    return gc.open('Lista_Casamento')

# Tenta carregar as duas abas
try:
    planilha = conectar_planilha()
    aba_convidados = planilha.worksheet('Convidados')
    aba_gastos = planilha.worksheet('Gastos')
except Exception as e:
    st.error("⚠️ Erro ao conectar. Verifique se você renomeou as abas da planilha lá no Google para 'Convidados' e 'Gastos'.")
    st.stop()

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação:", ["📋 Lista de Convidados", "💰 Controle de Gastos"])

# ==========================================
#        PÁGINA 1: CONVIDADOS
# ==========================================
if menu == "📋 Lista de Convidados":
    st.title("💍 Gerenciador de Lista de Casamento")

    with st.form("cadastro", clear_on_submit=True):
        st.subheader("Adicionar Novo Convite")
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do titular do convite")
            categoria = st.selectbox("Grupo/Categoria:", ["Padrinho", "Madrinha", "Família da Noiva", "Família do Noivo", "Amigos"])
        with col2:
            acompanhantes = st.number_input("Acompanhantes extras", min_value=0, max_value=10, value=0)
            confirmado = st.selectbox("Status de Presença:", ["Pendente", "Sim", "Não"])
            
        botao = st.form_submit_button("Salvar Convite")

        if botao and nome:
            aba_convidados.append_row([nome, categoria, acompanhantes, confirmado])
            st.success(f"Convite para {nome} salvo com sucesso!")

    st.divider()
    
    dados = aba_convidados.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        st.subheader("📋 Lista Completa")
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("A lista ainda está vazia.")

# ==========================================
#        PÁGINA 2: CONTROLE DE GASTOS
# ==========================================
elif menu == "💰 Controle de Gastos":
    st.title("💰 Orçamento do Casamento")

    # Formulário de Gastos
    with st.form("cadastro_gasto", clear_on_submit=True):
        st.subheader("Registrar Novo Pagamento ou Orçamento")
        col1, col2 = st.columns(2)
        
        with col1:
            item = st.text_input("Item / Serviço (ex: Fotógrafo, Flores)")
            categoria = st.selectbox("Categoria do Gasto:", ["Cerimônia", "Festa", "Roupas e Maquiagem", "Papelaria", "Lua de Mel", "Outros"])
        with col2:
            valor_previsto = st.number_input("Valor Total/Previsto (R$)", min_value=0.0, format="%.2f")
            valor_pago = st.number_input("Valor Já Pago (R$)", min_value=0.0, format="%.2f")
            status = st.selectbox("Status:", ["Pendente", "Pago Parcial", "Quitado"])
        
        botao_gasto = st.form_submit_button("Salvar Despesa")

        if botao_gasto and item:
            aba_gastos.append_row([item, categoria, valor_previsto, valor_pago, status])
            st.success(f"Gasto com '{item}' registrado!")

    st.divider()

    # Exibir Tabela de Gastos e Matemática
    dados_gastos = aba_gastos.get_all_records()
    if dados_gastos:
        df_gastos = pd.DataFrame(dados_gastos)
        
        # Converte os valores para números para podermos fazer as contas
        df_gastos['Valor Previsto'] = pd.to_numeric(df_gastos['Valor Previsto'], errors='coerce').fillna(0)
        df_gastos['Valor Pago'] = pd.to_numeric(df_gastos['Valor Pago'], errors='coerce').fillna(0)
        
        total_previsto = df_gastos['Valor Previsto'].sum()
        total_pago = df_gastos['Valor Pago'].sum()
        falta_pagar = total_previsto - total_pago

        # --- NOVIDADE: BARRA DE PROGRESSO DO TETO GERAL ---
        st.subheader("🎯 Meta do Orçamento Geral")
        teto_geral = st.number_input("Qual o Teto Máximo que vocês pretendem gastar no total? (R$)", min_value=1.0, value=30000.0, step=1000.0)
        
        porcentagem_uso = (total_previsto / teto_geral) * 100
        
        # Desenha a barra (trava no máximo de 100% visualmente)
        st.progress(min(porcentagem_uso / 100, 1.0)) 
        
        if porcentagem_uso > 100:
            st.error(f"⚠️ Atenção! O valor previsto total (R$ {total_previsto:,.2f}) já ultrapassou o teto do orçamento em {porcentagem_uso - 100:.1f}%!")
        else:
            st.success(f"✅ O planejamento atual compromete {porcentagem_uso:.1f}% do teto geral.")

        st.divider()

        # Painel de Resumo
        st.subheader("📊 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento Total (Previsto)", f"R$ {total_previsto:,.2f}")
        c2.metric("Total Já Pago", f"R$ {total_pago:,.2f}")
        c3.metric("Falta Pagar", f"R$ {falta_pagar:,.2f}")

        # --- GRÁFICOS ---
        st.divider()
        st.subheader("📈 Visão Geral do Orçamento")
        
        col_grafico1, col_grafico2 = st.columns(2)
        
        with col_grafico1:
            st.caption("Status Geral do Dinheiro (R$)")
            df_resumo = pd.DataFrame({
                "Status": ["Total Previsto", "Total Pago", "Falta Pagar"],
                "Valores": [total_previsto, total_pago, falta_pagar]
            }).set_index("Status")
            st.bar_chart(df_resumo)
            
        with col_grafico2:
            st.caption("Comparativo: Previsto vs Pago por Categoria (R$)")
            # --- NOVIDADE: AGRUPANDO DUAS COLUNAS PARA COMPARAR LADO A LADO ---
            gastos_por_categoria = df_gastos.groupby("Categoria")[["Valor Previsto", "Valor Pago"]].sum()
            st.bar_chart(gastos_por_categoria)

        st.divider()
        st.subheader("🧾 Extrato de Despesas")
        st.dataframe(df_gastos, hide_index=True, use_container_width=True)
    else:
        st.info("Ainda não há gastos registrados. Comece adicionando o primeiro orçamento acima!")
