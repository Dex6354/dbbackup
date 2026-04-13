import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd
import io
import shutil

st.set_page_config(page_title="Music Database Editor", layout="wide")

# Estilização para uma interface limpa
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎵 Editor de Music Database")

# Inicialização do diretório de trabalho
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = "temp_workspace"
    if not os.path.exists(st.session_state.temp_dir):
        os.makedirs(st.session_state.temp_dir)

# Sidebar para Upload
uploaded_file = st.sidebar.file_uploader("Upload do arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    base_name = os.path.splitext(uploaded_file.name)[0]
    new_filename = f"{base_name}_novo.backup"
    
    # Processamento do ZIP
    if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(st.session_state.temp_dir)
            st.session_state.all_files = zip_ref.namelist()
            
            # Lógica de busca: Music Database (iniciais maiúsculas) ou song.db (minúsculo)
            st.session_state.db_filename = next(
                (f for f in st.session_state.all_files if f == "Music Database" or f == "song.db"), 
                None
            )
            st.session_state.current_file = uploaded_file.name

    if st.session_state.db_filename:
        db_path = os.path.join(st.session_state.temp_dir, st.session_state.db_filename)
        conn = sqlite3.connect(db_path)
        
        # Carregar Tabelas
        query_tables = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        tables = pd.read_sql_query(query_tables, conn)['name'].tolist()
        
        st.sidebar.subheader("Navegação")
        selected_table = st.sidebar.radio(f"Tabelas em {st.session_state.db_filename}:", tables)

        tab1, tab2 = st.tabs(["📝 Editar Dados", "📊 Estrutura da Tabela"])

        with tab1:
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            st.write(f"Editando registros de: **{selected_table}**")
            
            # Editor de dados (permite apagar células e adicionar linhas)
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
            
            if st.button("Aplicar Alterações"):
                try:
                    # Resolve o erro de células vazias convertendo NaN para string vazia
                    final_df = edited_df.fillna("") 
                    final_df.to_sql(selected_table, conn, if_exists='replace', index=False)
                    st.success(f"Alterações salvas em {st.session_state.db_filename}!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        with tab2:
            info = pd.read_sql_query(f"PRAGMA table_info('{selected_table}')", conn)
            st.table(info[['name', 'type', 'notnull', 'pk']])

        conn.close()

        # Exportação
        st.sidebar.divider()
        st.sidebar.subheader("Exportar")
        
        if st.sidebar.button("📦 Gerar Backup Atualizado"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                for file in st.session_state.all_files:
                    file_path = os.path.join(st.session_state.temp_dir, file)
                    if os.path.exists(file_path):
                        new_zip.write(file_path, arcname=file)
            
            st.sidebar.download_button(
                label="⬇️ Baixar .backup",
                data=buf.getvalue(),
                file_name=new_filename,
                mime="application/octet-stream"
            )
    else:
        st.error("Arquivo 'Music Database' ou 'song.db' não encontrado no backup.")
else:
    st.info("Aguardando upload do arquivo para carregar os dados...")
