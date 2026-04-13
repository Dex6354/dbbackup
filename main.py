import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd
import io
import shutil

# Configurações iniciais
st.set_page_config(page_title="Music Database Editor Pro", layout="wide")

# Estilo para abas e interface
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    .main { background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎵 Music Database & song.db Editor")

# Inicialização do workspace temporário no session_state
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = "temp_workspace"
    if os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)
    os.makedirs(st.session_state.temp_dir)

# Sidebar para Upload e Controles
st.sidebar.header("📁 Arquivo")
uploaded_file = st.sidebar.file_uploader("Upload do arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    # Definindo nomes de saída
    base_name = os.path.splitext(uploaded_file.name)[0]
    new_filename = f"{base_name}_novo.backup"
    
    # Processamento e Extração (Apenas se o arquivo mudar)
    if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
        # Limpa pasta temporária anterior
        for f in os.listdir(st.session_state.temp_dir):
            os.remove(os.path.join(st.session_state.temp_dir, f))
            
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(st.session_state.temp_dir)
            st.session_state.all_files = zip_ref.namelist()
            
            # Busca prioritária pelos nomes específicos
            st.session_state.db_filename = next(
                (f for f in st.session_state.all_files if f == "Music Database" or f == "song.db"), 
                None
            )
            st.session_state.current_file = uploaded_file.name

    if st.session_state.db_filename:
        db_path = os.path.join(st.session_state.temp_dir, st.session_state.db_filename)
        
        # Conexão com o banco
        conn = sqlite3.connect(db_path)
        
        # Listar Tabelas
        query_tables = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        tables = pd.read_sql_query(query_tables, conn)['name'].tolist()
        
        st.sidebar.subheader("Navegação")
        selected_table = st.sidebar.radio(f"Tabelas encontradas:", tables)

        # Abas de visualização
        tab1, tab2 = st.tabs(["📝 Editar Dados", "📊 Estrutura (Schema)"])

        with tab1:
            # Carregar dados
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            st.subheader(f"Tabela: {selected_table}")
            
            # Data Editor com suporte a linhas dinâmicas
            edited_df = st.data_editor(
                df, 
                use_container_width=True, 
                hide_index=True, 
                num_rows="dynamic"
            )
            
            if st.button("💾 Aplicar Alterações na Tabela"):
                try:
                    # TRATAMENTO DE CÉLULAS VAZIAS:
                    # Converte strings vazias, espaços e NaNs em None (NULL para o SQLite)
                    final_df = edited_df.replace({"": None, " ": None})
                    final_df = final_df.where(pd.notnull(final_df), None)
                    
                    # Salva no banco de dados temporário
                    final_df.to_sql(selected_table, conn, if_exists='replace', index=False)
                    
                    st.success(f"Dados salvos com sucesso em '{st.session_state.db_filename}'!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        with tab2:
            st.subheader("Informações das Colunas")
            info = pd.read_sql_query(f"PRAGMA table_info('{selected_table}')", conn)
            st.table(info[['name', 'type', 'notnull', 'pk']])

        conn.close()

        # Seção de Download na Sidebar
        st.sidebar.divider()
        st.sidebar.subheader("📦 Finalizar")
        
        if st.sidebar.button("Preparar Download"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                # Re-empacota TODOS os arquivos originais + o banco editado
                for file in st.session_state.all_files:
                    file_path = os.path.join(st.session_state.temp_dir, file)
                    if os.path.exists(file_path):
                        new_zip.write(file_path, arcname=file)
            
            st.sidebar.download_button(
                label="📥 Baixar .backup Atualizado",
                data=buf.getvalue(),
                file_name=new_filename,
                mime="application/octet-stream"
            )
    else:
        st.error("Erro: Não encontramos 'Music Database' ou 'song.db' dentro do arquivo enviado.")
else:
    st.info("👈 Por favor, faça o upload do seu arquivo .backup para começar.")
    st.markdown("""
    ### Instruções:
    1. Suba seu arquivo na barra lateral.
    2. Selecione a tabela que deseja editar.
    3. Para deixar uma célula **NULL**, basta apagar o conteúdo dela.
    4. Após editar, clique em **Aplicar Alterações**.
    5. Por fim, use o botão de **Preparar Download** na lateral.
    """)
