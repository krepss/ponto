import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Análise de Banco de Horas",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Analisador de Banco de Horas")
st.markdown("Sistema inteligente configurado com tabelas coloridas para facilitar a gestão do banco de horas.")

# Função robusta para converter formato de hora (ex: 02:30, -05:56, +00:13) para número decimal
def limpar_e_converter_hora(valor):
    if pd.isna(valor):
        return 0.0
    
    texto = str(valor).strip().replace(' ', '')
    
    if not texto or texto in ['0', '0.0', '0,0', '00:00']:
        return 0.0
    
    negativo = False
    if texto.startswith('-'):
        negativo = True
        texto = texto.replace('-', '')
    elif texto.startswith('+'):
        texto = texto.replace('+', '')
        
    if ':' in texto:
        try:
            partes = texto.split(':')
            horas = int(partes[0])
            minutos = int(partes[1]) if len(partes) > 1 else 0
            decimal = horas + (minutos / 60.0)
            return -decimal if negativo else decimal
        except:
            return 0.0
            
    if ',' in texto:
        texto = texto.replace(',', '.')
        
    try:
        decimal = float(texto)
        return -decimal if negativo else decimal
    except:
        return 0.0

# Funções de estilização de cores para o Pandas DataFrame
def colorir_saldo(val):
    """
    Analisa o texto do saldo. Se começar com '-', pinta de vermelho suave.
    Se começar com '+' ou for positivo, pinta de verde suave.
    """
    texto = str(val).strip()
    if texto.startswith('-'):
        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
    elif texto.startswith('+') or (texto != '00:00' and not texto.startswith('0')):
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    return ''

# 1. Área de Upload
uploaded_file = st.file_uploader("Arraste e solte seu relatório de horas aqui (Excel ou CSV):", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=4)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
            
        df.columns = df.columns.str.strip()
        colunas_no_df = df.columns.tolist()
        
        col_nome = next((c for c in colunas_no_df if c.lower() in ['nome', 'colaborador', 'funcionario', 'funcionário']), colunas_no_df[0])
        col_saldo_atual = next((c for c in colunas_no_df if c.lower() in ['total banco', 'saldo atual', 'saldo final', 'saldo']), None)
        col_saldo_periodo = next((c for c in colunas_no_df if c.lower() in ['saldo do período', 'saldo do periodo', 'saldo período', 'saldo periodo']), None)
        
        if not col_saldo_atual:
            col_saldo_atual = colunas_no_df[-1]
            
        df = df.dropna(subset=[col_nome])
        df = df[~df[col_nome].astype(str).str.contains('TOTAL', case=False, na=False)]
        
        col_saldo_atual_num = f"{col_saldo_atual}_Num"
        df[col_saldo_atual_num] = df[col_saldo_atual].apply(limpar_e_converter_hora)
        
        if col_saldo_periodo and col_saldo_periodo in df.columns:
            col_saldo_periodo_num = f"{col_saldo_periodo}_Num"
            df[col_saldo_periodo_num] = df[col_saldo_periodo].apply(limpar_e_converter_hora)

        st.success(f"✅ Sucesso! {len(df)} colaboradores processados.")

        positivos = df[df[col_saldo_atual_num] > 0].sort_values(by=col_saldo_atual_num, ascending=False)
        negativos = df[df[col_saldo_atual_num] < 0].sort_values(by=col_saldo_atual_num, ascending=True)

        # --- Bloco 1: Indicadores e Métricas ---
        st.subheader("📊 Resumo Consolidado do Banco de Horas")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Total de Colaboradores", len(df))
        m2.metric("Saldos Positivos (Crédito)", len(positivos), f"📈 {len(positivos)} pessoas")
        m3.metric("Saldos Negativos (Dívida)", len(negativos), f"📉 {len(negativos)} pessoas", delta_color="inverse")
        
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
                st.info("Nenhum colaborador com saldo positivo.")
                
        with col_graf2:
            st.subheader("📉 Top Colaboradores com Mais Horas Negativas")
            if not negativos.empty:
                df_neg_grafico = negativos.head(10).sort_values(by=col_saldo_atual_num, ascending=False).set_index(col_nome)
                st.bar_chart(df_neg_grafico[col_saldo_atual_num], horizontal=True)
            else:
                st.info("Nenhum colaborador com saldo negativo.")

        st.markdown("---")

        # --- Bloco 3: Tabelas de Dados Organizadas por Abas ---
        tab_pos, tab_neg, tab_geral = st.tabs(["🟢 Credores (Positivos)", "🔴 Devedores (Negativos)", "📋 Todos os Dados"])
        
        colunas_exibicao = [c for c in colunas_no_df if not c.endswith('_Num')]
        
        with tab_pos:
            st.markdown(f"### Lista de Colaboradores com Horas a Favor")
            # Aplica a cor apenas na coluna de Saldo Atual para ficar elegante
            df_colorido_pos = positivos[colunas_exibicao].style.map(colorir_saldo, subset=[col_saldo_atual])
            st.dataframe(df_colorido_pos, use_container_width=True)
            
        with tab_neg:
            st.markdown(f"### Lista de Colaboradores que Devem Horas")
            df_colorido_neg = negativos[colunas_exibicao].style.map(colorir_saldo, subset=[col_saldo_atual])
            st.dataframe(df_colorido_neg, use_container_width=True)
            
        with tab_geral:
            st.markdown("### Relatório Completo (Cores aplicadas no Saldo do Período e Total Banco)")
            # No relatório geral, colore tanto o saldo do mês quanto o saldo final acumulado
            colunas_para_colorir = [c for c in [col_saldo_periodo, col_saldo_atual] if c is not None]
            df_colorido_geral = df[colunas_exibicao].style.map(colorir_saldo, subset=colunas_para_colorir)
            st.dataframe(df_colorido_geral, use_container_width=True)

    except Exception as e:
        st.error(f"Erro inesperado no processamento: {e}")
else:
    st.info("💡 Aguardando o upload do seu relatório de ponto para gerar a análise.")
