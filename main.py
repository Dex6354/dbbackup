import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd
import io
import shutil

st.set_page_config(page_title="SQLite Editor Pro", layout="wide")

# Estilo para melhorar a visualização
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎵 Editor de Backup de Música")

# Inicialização do estado
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = "temp_workspace"
    if os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)
    os.makedirs(st.session_state.temp_dir)

# Sidebar
uploaded_file = st.sidebar.file_uploader("Upload do arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    base_name = os.path.splitext(uploaded_file.name)[0]
    new_filename = f"{base_name}_novo.backup"
    
    # Extração e mapeamento de arquivos
    # Usamos o estado para não re-extrair a cada clique
    if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(st.session_state.temp_dir)
            st.session_state.all_files = zip_ref.namelist()
            # Tenta encontrar o DB
            st.session_state.db_filename = next((f for f in st.session_state.all_files if f in ["song.db", "music database"]), None)
            st.session_state.current_file = uploaded_file.name

    if st.session_state.db_filename:
        db_path = os.path.join(st.session_state.temp_dir, st.session_state.db_filename)
        conn = sqlite3.connect(db_path)
        
        # Listagem de Tabelas
        query_tables = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        tables = pd.read_sql_query(query_tables, conn)['name'].tolist()
        
        st.sidebar.subheader("Navegação")
        selected_table = st.sidebar.radio("Tabelas encontradas:", tables)

        tab1, tab2 = st.tabs(["📝 Editar Dados", "📊 Estrutura da Tabela"])

        with tab1:
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            st.write(f"Editando registros de: **{selected_table}**")
            
            # Editor de dados
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
            
            if st.button("Aplicar Alterações no Banco"):
                try:
                    edited_df.to_sql(selected_table, conn, if_exists='replace', index=False)
                    st.success("Alterações salvas no banco de dados temporário!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        with tab2:
            info = pd.read_sql_query(f"PRAGMA table_info('{selected_table}')", conn)
            st.table(info[['name', 'type', 'notnull', 'pk']])

        conn.close()

        # Botão de Exportação na Sidebar
        st.sidebar.divider()
        st.sidebar.subheader("Exportar Backup")
        
        if st.sidebar.button("📦 Gerar Novo Arquivo .backup"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                # Percorre TODOS os arquivos que estavam no ZIP original
                for file in st.session_state.all_files:
                    file_path = os.path.join(st.session_state.temp_dir, file)
                    if os.path.exists(file_path):
                        new_zip.write(file_path, arcname=file)
            
            st.sidebar.download_button(
                label="⬇️ Baixar Agora",
                data=buf.getvalue(),
                file_name=new_filename,
                mime="application/octet-stream"
            )
    else:
        st.error("O arquivo banco de dados não foi detectado dentro do backup.")
else:
    st.info("Aguardando upload do arquivo para carregar as tabelas...")
    # Limpa o estado se o arquivo for removido
    if 'current_file' in st.session_state:
        del st.session_state.current_file
