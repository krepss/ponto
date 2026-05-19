import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Analisador Inteligente de Arquivos",
    page_icon="📊",
    layout="wide"
)

# Título do App
st.title("📊 Analisador Inteligente de Arquivos")
st.markdown("Suba o seu arquivo abaixo para processar e analisar os dados automaticamente.")

# 1. Área de Upload do Arquivo
uploaded_file = st.file_uploader(
    "Escolha um arquivo (CSV ou Excel)", 
    type=["csv", "xlsx", "xls"]
)

# 2. Lógica de Processamento
if uploaded_file is not None:
    try:
        # Identifica a extensão e lê o arquivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("✅ Arquivo carregado com sucesso!")
        
        # Criação de abas para organizar a visualização
        tab1, tab2, tab3 = st.tabs(["👀 Visualização dos Dados", "📈 Insights & Análise", "⚙️ Exportar"])
        
        with tab1:
            st.subheader("Pré-visualização dos Dados")
            st.dataframe(df.head(10)) # Mostra as 10 primeiras linhas
            
            st.subheader("Informações Gerais")
            col1, col2 = st.columns(2)
            col1.metric("Total de Linhas", df.shape[0])
            col2.metric("Total de Colunas", df.shape[1])

        with tab2:
            st.subheader("Análise Automática")
            # Exemplo de insight automático (ajuste conforme sua necessidade)
            st.markdown("**Resumo Estatístico das Colunas Numéricas:**")
            st.dataframe(df.describe())
            
            # Espaço para os gráficos ou regras de negócio específicas que você precisar
            st.info("💡 Dica: Podemos programar alertas ou gráficos específicos aqui baseados no seu arquivo!")

        with tab3:
            st.subheader("Download dos Resultados")
            # Permite baixar o arquivo processado de volta se houver modificações
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar dados processados (CSV)",
                data=csv,
                file_name="dados_processados.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

else:
    st.info("💡 Aguardando o upload de um arquivo para iniciar a análise.")
