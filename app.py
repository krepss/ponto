import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Análise de Banco de Horas",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Analisador de Banco de Horas")
st.markdown(" Sistema configurado especificamente para o modelo de relatório da sua empresa.")

# 1. Área de Upload
uploaded_file = st.file_uploader("Arraste e solte o arquivo do banco de horas aqui:", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Lendo o arquivo pulando as 4 primeiras linhas de cabeçalho institucional
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=4)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
            
        # Limpeza: Remove linhas completamente vazias ou que sejam o totalizador do fim da planilha
        df = df.dropna(subset=['Nome'])
        df = df[~df['Nome'].str.contains('TOTAL', case=False, na=False)]
        
        # Garante que as colunas de saldo sejam numéricas
        colunas_horas = ['Saldo Anterior', 'Crédito Período', 'Débito Período', 'Saldo Atual']
        for col in colunas_horas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        st.success(f"✅ Sucesso! {len(df)} colaboradores processados.")

        # Separando os Saldos Atuais (Positivos vs Negativos)
        positivos = df[df['Saldo Atual'] > 0].sort_values(by='Saldo Atual', ascending=False)
        negativos = df[df['Saldo Atual'] < 0].sort_values(by='Saldo Atual', ascending=True)
        zerados = df[df['Saldo Atual'] == 0]

        # --- Bloco 1: Métricas de Impacto ---
        st.subheader("📊 Resumo do Banco de Horas Atual")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Total de Colaboradores", len(df))
        m2.metric("Saldos Positivos (Crédito)", len(positivos), f"📈 {len(positivos)} pessoas")
        m3.metric("Saldos Negativos (Dívida)", len(negatives), f"📉 {len(negativos)} pessoas", delta_color="inverse")
        m4.metric("Balanço Geral da Empresa", f"{df['Saldo Atual'].sum():.2f}h")

        st.markdown("---")

        # --- Bloco 2: Gráficos Visuais ---
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("📈 Top Colaboradores com Mais Horas Positivas")
            if not positivos.empty:
                # Gráfico de barras horizontais nativo do Streamlit
                df_pos_grafico = positivos.head(10).set_index('Nome')
                st.bar_chart(df_pos_grafico['Saldo Atual'], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo positivo.")
                
        with col_graf2:
            st.subheader("📉 Top Colaboradores com Mais Horas Negativas")
            if not negatives.empty:
                df_neg_grafico = negatives.head(10).set_index('Nome')
                st.bar_chart(df_neg_grafico['Saldo Atual'], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo negativo.")

        st.markdown("---")

        # --- Bloco 3: Listas Detalhadas ---
        tab_pos, tab_neg, tab_geral = st.tabs(["🟢 Credores (Positivos)", "🔴 Devedores (Negativos)", "📋 Todos os Dados"])
        
        # Formatação para exibição amigável nas tabelas
        colunas_exibicao = ['Nome', 'Saldo Anterior', 'Crédito Período', 'Débito Período', 'Saldo Atual']
        
        with tab_pos:
            st.markdown("### Colaboradores com horas a favor")
            st.dataframe(positivos[colunas_exibicao], use_container_width=True)
            
        with tab_neg:
            st.markdown("### Colaboradores que devem horas")
            st.dataframe(negativos[colunas_exibicao], use_container_width=True)
            
        with tab_geral:
            st.markdown("### Relatório Consolidado Limpo")
            st.dataframe(df[colunas_exibicao], use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao ler o layout do arquivo: {e}")
        st.info("Certifique-se de que o arquivo carregado segue o modelo padrão enviado.")
else:
    st.info("💡 Aguardando o upload do arquivo `Planilha_Saldo_Horas.csv` ou `.xlsx` para gerar os insights.")
