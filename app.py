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

try:
    planilha = conectar_planilha()
    aba_convidados = planilha.worksheet('Convidados')
    aba_gastos = planilha.worksheet('Gastos')
except Exception as e:
    st.error("⚠️ Erro ao conectar. Verifique as abas 'Convidados' e 'Gastos' no Google Sheets.")
    st.stop()

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação:", ["📋 Lista de Convidados", "💰 Controle de Gastos"])

# ==========================================
#        PÁGINA 1: CONVIDADOS
# ==========================================
if menu == "📋 Lista de Convidados":
    st.title("💍 Lista de Casamento")

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
            st.rerun() # Atualiza a página na mesma hora

    st.divider()
    
    dados = aba_convidados.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        st.subheader("📋 Lista Completa (Editável)")
        st.caption("💡 Dica: Dê dois cliques em uma célula para editar o texto. Para excluir uma pessoa, clique na caixinha à esquerda do nome dela e aperte o botão 'Delete' (ou o ícone da lixeira).")
        
        # --- NOVIDADE: TABELA INTERATIVA ---
        df_editado = st.data_editor(df, num_rows="dynamic", hide_index=True, use_container_width=True)
        
        # Botão para salvar as edições feitas na tabela
        if st.button("💾 Salvar Alterações na Lista"):
            with st.spinner("Salvando no Google..."):
                aba_convidados.clear() # Limpa a planilha antiga
                # Prepara os dados novos e salva
                dados_salvar = [df_editado.columns.values.tolist()] + df_editado.fillna("").values.tolist()
                aba_convidados.append_rows(dados_salvar)
                st.success("Planilha atualizada com sucesso!")
                st.rerun() # Recarrega para mostrar tudo atualizado
    else:
        st.info("A lista ainda está vazia.")

# ==========================================
#        PÁGINA 2: CONTROLE DE GASTOS
# ==========================================
elif menu == "💰 Controle de Gastos":
    st.title("💰 Orçamento do Casamento")

    with st.form("cadastro_gasto", clear_on_submit=True):
        st.subheader("Registrar Novo Pagamento")
        col1, col2 = st.columns(2)
        with col1:
            item = st.text_input("Item / Serviço")
            categoria = st.selectbox("Categoria:", ["Cerimônia", "Festa", "Roupas", "Dj","Espaço", "Buffet", "Fotografo", "Doces e Bolo" , "Lua de Mel", "Outros"])
        with col2:
            valor_previsto = st.number_input("Valor Previsto (R$)", min_value=0.0, format="%.2f")
            valor_pago = st.number_input("Valor Pago (R$)", min_value=0.0, format="%.2f")
            status = st.selectbox("Status:", ["Pendente", "Pago Parcial", "Quitado"])
        
        if st.form_submit_button("Salvar Despesa") and item:
            aba_gastos.append_row([item, categoria, valor_previsto, valor_pago, status])
            st.success(f"Gasto com '{item}' registrado!")
            st.rerun()

    st.divider()

    dados_gastos = aba_gastos.get_all_records()
    if dados_gastos:
        df_gastos = pd.DataFrame(dados_gastos)
        df_gastos['Valor Previsto'] = pd.to_numeric(df_gastos['Valor Previsto'], errors='coerce').fillna(0)
        df_gastos['Valor Pago'] = pd.to_numeric(df_gastos['Valor Pago'], errors='coerce').fillna(0)
        
        total_previsto = df_gastos['Valor Previsto'].sum()
        total_pago = df_gastos['Valor Pago'].sum()
        falta_pagar = total_previsto - total_pago

        st.subheader("🎯 Meta do Orçamento Geral")
        teto_geral = st.number_input("Qual o Teto Máximo total? (R$)", min_value=1.0, value=50000.0, step=1000.0)
        porcentagem_uso = (total_previsto / teto_geral) * 100
        st.progress(min(porcentagem_uso / 100, 1.0)) 
        
        if porcentagem_uso > 100:
            st.error(f"⚠️ Atenção! O valor previsto total já ultrapassou o teto em {porcentagem_uso - 100:.1f}%!")
        else:
            st.success(f"✅ O planejamento atual compromete {porcentagem_uso:.1f}% do teto geral.")

        st.divider()
        st.subheader("📊 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento Total", f"R$ {total_previsto:,.2f}")
        c2.metric("Total Já Pago", f"R$ {total_pago:,.2f}")
        c3.metric("Falta Pagar", f"R$ {falta_pagar:,.2f}")

        st.divider()
        st.subheader("📈 Visão Geral do Orçamento")
        col_grafico1, col_grafico2 = st.columns(2)
        with col_grafico1:
            st.bar_chart(pd.DataFrame({"Status": ["Previsto", "Pago", "Falta Pagar"], "Valores": [total_previsto, total_pago, falta_pagar]}).set_index("Status"))
        with col_grafico2:
            st.bar_chart(df_gastos.groupby("Categoria")[["Valor Previsto", "Valor Pago"]].sum())

        st.divider()
        st.subheader("🧾 Extrato de Despesas (Editável)")
        st.caption("💡 Dica: Altere os valores pagos diretamente na tabela abaixo. Para excluir, selecione a linha e apague. Depois clique em Salvar!")
        
        # --- NOVIDADE: TABELA INTERATIVA DE GASTOS ---
        df_gastos_editado = st.data_editor(df_gastos, num_rows="dynamic", hide_index=True, use_container_width=True)
        
        if st.button("💾 Salvar Alterações nos Gastos"):
            with st.spinner("Atualizando gráfico e planilhas..."):
                aba_gastos.clear()
                dados_salvar_gastos = [df_gastos_editado.columns.values.tolist()] + df_gastos_editado.fillna("").values.tolist()
                aba_gastos.append_rows(dados_salvar_gastos)
                st.success("Alterações financeiras salvas com sucesso!")
                st.rerun() # Atualiza os gráficos imediatamente!
    else:
        st.info("Ainda não há gastos registrados.")


