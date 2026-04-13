import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd
import io

st.set_page_config(page_title="SQLite Editor", layout="wide")

st.title("📝 SQLite Editor & Packager")

# Inicializar o estado da sessão para armazenar o caminho do DB temporário
if 'db_path' not in st.session_state:
    st.session_state.db_path = None
if 'db_filename' not in st.session_state:
    st.session_state.db_filename = None

# Sidebar
uploaded_file = st.sidebar.file_uploader("Suba seu arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    temp_dir = "temp_db"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Processar o arquivo apenas uma vez
    if st.session_state.db_path is None:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            db_name = next((f for f in file_list if f in ["song.db", "music database"]), None)

            if db_name:
                extract_path = zip_ref.extract(db_name, temp_dir)
                st.session_state.db_path = extract_path
                st.session_state.db_filename = db_name
            else:
                st.error("Arquivo de banco de dados não encontrado no ZIP.")

    if st.session_state.db_path:
        conn = sqlite3.connect(st.session_state.db_path)
        
        # Listar tabelas
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';", conn)['name'].tolist()
        selected_table = st.sidebar.radio("Selecione a Tabela:", tables)

        # Abas
        tab1, tab2 = st.tabs(["✏️ Editar Dados", "🏗️ Estrutura"])

        with tab1:
            df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
            
            st.subheader(f"Editando: {selected_table}")
            st.info("Dica: Clique duplo na célula para editar. As alterações são salvas ao clicar no botão abaixo.")
            
            # Componente de edição
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")

            if st.button("Salvar Alterações no Banco"):
                try:
                    # Salva o DataFrame de volta no SQLite (substitui a tabela)
                    edited_df.to_sql(selected_table, conn, if_exists='replace', index=False)
                    st.success(f"Tabela '{selected_table}' atualizada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        with tab2:
            cols_info = pd.read_sql_query(f"PRAGMA table_info('{selected_table}')", conn)
            st.table(cols_info[['name', 'type', 'pk']])

        conn.close()

        # Seção de Download (Exportar .backup)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Exportar")
        
        if st.sidebar.button("Preparar Download"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                # Adiciona o arquivo DB modificado para dentro do novo zip
                new_zip.write(st.session_state.db_path, arcname=st.session_state.db_filename)
            
            st.sidebar.download_button(
                label="📥 Baixar .backup Atualizado",
                data=buf.getvalue(),
                file_name="novo_arquivo.backup",
                mime="application/zip"
            )

else:
    st.session_state.db_path = None
    st.info("👈 Faça upload do arquivo para começar a editar.")
