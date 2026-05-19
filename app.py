import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Análise de Banco de Horas",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Analisador de Banco de Horas")
st.markdown("Sistema inteligente configurado para ler relatórios de controle de ponto e banco de horas.")

# Função robusta para converter formato de hora (ex: 02:30, -05:56, +00:13) para número decimal
def limpar_e_converter_hora(valor):
    if pd.isna(valor):
        return 0.0
    
    # Remove espaços e padroniza o texto
    texto = str(valor).strip().replace(' ', '')
    
    if not texto or texto in ['0', '0.0', '0,0', '00:00']:
        return 0.0
    
    negativo = False
    if texto.startswith('-'):
        negativo = True
        texto = texto.replace('-', '')
    elif texto.startswith('+'):
        texto = texto.replace('+', '')
        
    # Formato de Relógio do Ponto (HH:MM ou HH:MM:SS)
    if ':' in texto:
        try:
            partes = texto.split(':')
            horas = int(partes[0])
            minutos = int(partes[1]) if len(partes) > 1 else 0
            decimal = horas + (minutos / 60.0)
            return -decimal if negativo else decimal
        except:
            return 0.0
            
    # Formato Decimal com vírgula padrão nacional (ex: 5,50)
    if ',' in texto:
        texto = texto.replace(',', '.')
        
    try:
        decimal = float(texto)
        return -decimal if negativo else decimal
    except:
        return 0.0

# 1. Área de Upload
uploaded_file = st.file_uploader("Arraste e solte seu relatório de horas aqui (Excel ou CSV):", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Lendo o arquivo pulando as 4 primeiras linhas de cabeçalho institucional
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=4)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
            
        # Limpa os espaços em branco extras das pontas dos nomes das colunas
        df.columns = df.columns.str.strip()
        colunas_no_df = df.columns.tolist()
        
        # Mapeamento Dinâmico e Inteligente das Colunas Encontradas
        col_nome = next((c for c in colunas_no_df if c.lower() in ['nome', 'colaborador', 'funcionario', 'funcionário']), colunas_no_df[0])
        col_saldo_atual = next((c for c in colunas_no_df if c.lower() in ['total banco', 'saldo atual', 'saldo final', 'saldo']), None)
        col_saldo_periodo = next((c for c in colunas_no_df if c.lower() in ['saldo do período', 'saldo do periodo', 'saldo período', 'saldo periodo']), None)
        
        # Se não encontrar nenhuma palavra-chave, assume a última coluna do arquivo como o saldo consolidado
        if not col_saldo_atual:
            col_saldo_atual = colunas_no_df[-1]
            
        # Limpeza: Remove linhas vazias e evita que linhas de totais quebrem o cálculo
        df = df.dropna(subset=[col_nome])
        df = df[~df[col_nome].astype(str).str.contains('TOTAL', case=False, na=False)]
        
        # Cria colunas numéricas de controle interno para ordenar e gerar os gráficos
        col_saldo_atual_num = f"{col_saldo_atual}_Num"
        df[col_saldo_atual_num] = df[col_saldo_atual].apply(limpar_e_converter_hora)
        
        if col_saldo_periodo and col_saldo_periodo in df.columns:
            col_saldo_periodo_num = f"{col_saldo_periodo}_Num"
            df[col_saldo_periodo_num] = df[col_saldo_periodo].apply(limpar_e_converter_hora)

        st.success(f"✅ Sucesso! {len(df)} colaboradores processados com base na coluna de saldo encontrada: '{col_saldo_atual}'.")

        # Separando os saldos com base no número decimal calculado
        positivos = df[df[col_saldo_atual_num] > 0].sort_values(by=col_saldo_atual_num, ascending=False)
        negativos = df[df[col_saldo_atual_num] < 0].sort_values(by=col_saldo_atual_num, ascending=True)

        # --- Bloco 1: Indicadores e Métricas ---
        st.subheader("📊 Resumo Consolidado do Banco de Horas")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Total de Colaboradores", len(df))
        m2.metric("Saldos Positivos (Crédito)", len(positivos), f"📈 {len(positivos)} pessoas")
        m3.metric("Saldos Negativos (Dívida)", len(negativos), f"📉 {len(negativos)} pessoas", delta_color="inverse")
        
        # Calcula o saldo geral líquido de toda a empresa
        saldo_geral_empresa = df[col_saldo_atual_num].sum()
        m4.metric("Balanço Geral da Empresa", f"{saldo_geral_empresa:.2f}h")

        st.markdown("---")

        # --- Bloco 2: Gráficos Visuais de Barras ---
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("📈 Top Colaboradores com Mais Horas Positivas")
            if not positivos.empty:
                df_pos_grafico = positivos.head(10).set_index(col_nome)
                st.bar_chart(df_pos_grafico[col_saldo_atual_num], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo positivo no momento.")
                
        with col_graf2:
            st.subheader("📉 Top Colaboradores com Mais Horas Negativas")
            if not negativos.empty:
                # Ordena para exibir o gráfico de forma harmônica (do mais negativo para o menos negativo)
                df_neg_grafico = negativos.head(10).sort_values(by=col_saldo_atual_num, ascending=False).set_index(col_nome)
                st.bar_chart(df_neg_grafico[col_saldo_atual_num], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo negativo no momento.")

        st.markdown("---")

        # --- Bloco 3: Tabelas de Dados Organizadas por Abas ---
        tab_pos, tab_neg, tab_geral = st.tabs(["🟢 Credores (Positivos)", "🔴 Devedores (Negativos)", "📋 Todos os Dados"])
        
        # Filtra para exibir apenas as colunas originais limpas (esconde as colunas numéricas de controle interno)
        colunas_exibicao = [c for c in colunas_no_df if not c.endswith('_Num')]
        
        with tab_pos:
            st.markdown(f"### Lista de Colaboradores com Horas a Favor (Coluna de referência: {col_saldo_atual})")
            st.dataframe(positivos[colunas_exibicao], use_container_width=True)
            
        with tab_neg:
            st.markdown(f"### Lista de Colaboradores que Devem Horas (Coluna de referência: {col_saldo_atual})")
            st.dataframe(negativos[colunas_exibicao], use_container_width=True)
            
        with tab_geral:
            st.markdown("### Relatório Completo Lido do Arquivo")
            st.dataframe(df[colunas_exibicao], use_container_width=True)

    except Exception as e:
        st.error(f"Erro inesperado no processamento: {e}")
else:
    st.info("💡 Aguardando o upload do seu relatório de ponto para gerar a análise.")
