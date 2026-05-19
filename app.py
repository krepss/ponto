import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Análise de Banco de Horas",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Analisador de Banco de Horas")
st.markdown("Sistema configurado especificamente para o modelo de relatório da sua empresa.")

# Função robusta para converter qualquer formato de hora/texto para decimal
def limpar_e_converter_hora(valor):
    if pd.isna(valor):
        return 0.0
    
    # Transforma em string e limpa espaços
    texto = str(valor).strip().replace(' ', '')
    
    if not texto or texto == '0' or texto == '0.0' or texto == '0,0':
        return 0.0
    
    negativo = False
    if texto.startswith('-'):
        negativo = True
        texto = texto.replace('-', '')
        
    # Cenário 1: Formato de Relógio (HH:MM ou HH:MM:SS)
    if ':' in texto:
        try:
            partes = texto.split(':')
            horas = int(partes[0])
            minutos = int(partes[1]) if len(partes) > 1 else 0
            decimal = horas + (minutos / 60.0)
            return -decimal if negativo else decimal
        except:
            return 0.0
            
    # Cenário 2: Formato Decimal com vírgula (ex: 5,50 ou -2,25)
    if ',' in texto:
        texto = texto.replace(',', '.')
        
    try:
        decimal = float(texto)
        return -decimal if negativo else decimal
    except:
        return 0.0

# 1. Área de Upload
uploaded_file = st.file_uploader("Arraste e solte o arquivo do banco de horas aqui:", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Lendo o arquivo pulando as 4 primeiras linhas de cabeçalho institucional
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=4)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
            
        # Remove espaços invisíveis dos cabeçalhos
        df.columns = df.columns.str.strip()
        
        # Identifica a coluna do Nome do colaborador
        col_nome = 'Nome' if 'Nome' in df.columns else df.columns[0]
        
        # Limpeza: Remove linhas vazias ou totalizadores
        df = df.dropna(subset=[col_nome])
        df = df[~df[col_nome].astype(str).str.contains('TOTAL', case=False, na=False)]
        
        # Cria cópias das colunas originais formatadas para exibição bonita na tabela
        colunas_horas = ['Saldo Anterior', 'Crédito Período', 'Débito Período', 'Saldo Atual']
        
        # Aplica a conversão mágica coluna por coluna
        for col in colunas_horas:
            if col in df.columns:
                # Mantém o texto original para mostrar na tabela, mas cria uma versão numérica para os cálculos/gráficos
                df[f'{col}_Num'] = df[col].apply(limpar_e_converter_hora)
            else:
                df[f'{col}_Num'] = 0.0
                df[col] = "00:00"

        st.success(f"✅ Sucesso! {len(df)} colaboradores processados.")

        # Separando os Saldos Atuais com base nas novas colunas numéricas calculadas
        positivos = df[df['Saldo Atual..._Num' if 'Saldo Atual_Num' in df.columns else 'Saldo Atual_Num'] > 0].sort_values(by='Saldo Atual_Num', ascending=False)
        negativos = df[df['Saldo Atual_Num'] < 0].sort_values(by='Saldo Atual_Num', ascending=True)

        # --- Bloco 1: Métricas de Impacto ---
        st.subheader("📊 Resumo do Banco de Horas Atual")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Total de Colaboradores", len(df))
        m2.metric("Saldos Positivos (Crédito)", len(positivos), f"📈 {len(positivos)} pessoas")
        m3.metric("Saldos Negativos (Dívida)", len(negativos), f"📉 {len(negativos)} pessoas", delta_color="inverse")
        m4.metric("Balanço Geral da Empresa", f"{df['Saldo Atual_Num'].sum():.2f}h")

        st.markdown("---")

        # --- Bloco 2: Gráficos Visuais ---
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("📈 Top Colaboradores com Mais Horas Positivas")
            if not positivos.empty:
                df_pos_grafico = positivos.head(10).set_index(col_nome)
                st.bar_chart(df_pos_grafico['Saldo Atual_Num'], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo positivo.")
                
        with col_graf2:
            st.subheader("📉 Top Colaboradores com Mais Horas Negativas")
            if not negativos.empty:
                df_neg_grafico = negativos.head(10).set_index(col_nome)
                st.bar_chart(df_neg_grafico['Saldo Atual_Num'], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo negativo.")

        st.markdown("---")

        # --- Bloco 3: Listas Detalhadas ---
        tab_pos, tab_neg, tab_geral = st.tabs(["🟢 Credores (Positivos)", "🔴 Devedores (Negativos)", "📋 Todos os Dados"])
        
        # Colunas que vamos exibir na tabela final (exibindo os valores originais bonitinhos do seu arquivo)
        colunas_exibicao = [col_nome] + colunas_horas
        
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
        st.error(f"Erro inesperado no processamento: {e}")
else:
    st.info("💡 Aguardando o upload do arquivo para gerar os insights.")
