import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd

# Configuração da página
st.set_page_config(page_title="SQLite Backup Viewer", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stTable { background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 SQLite Web Viewer (.backup)")

uploaded_file = st.sidebar.file_uploader("Suba seu arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    temp_dir = "temp_db"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            db_filename = next((f for f in file_list if f in ["song.db", "Music Database"]), None)

            if db_filename:
                zip_ref.extract(db_filename, temp_dir)
                db_path = os.path.join(temp_dir, db_filename)
                
                # Conexão com modo isolation_level=None para autocommit ou gerenciar manualmente
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # --- OPERAÇÃO DE LIMPEZA E INSERÇÃO ---
                # Exemplo de IDs capturados (Substitua pela sua lista real de IDs)
                captured_ids = ["id_1", "id_2", "id_3"] 

                if st.sidebar.button("Limpar e Atualizar Tabela Song"):
                    try:
                        # 1. Limpa a tabela mantendo a estrutura
                        cursor.execute("DELETE FROM song")
                        
                        # 2. Insere os novos IDs na coluna videoId
                        for s_id in captured_ids:
                            cursor.execute("INSERT INTO song (videoId) VALUES (?)", (s_id,))
                        
                        conn.commit()
                        st.sidebar.success("Tabela 'song' atualizada com sucesso!")
                    except Exception as ex:
                        st.sidebar.error(f"Erro na transação: {ex}")
                # ---------------------------------------

                query_tables = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                tables = pd.read_sql_query(query_tables, conn)['name'].tolist()

                if tables:
                    st.sidebar.subheader("Tabelas")
                    selected_table = st.sidebar.radio("Selecione para visualizar:", tables)
                    columns_info = pd.read_sql_query(f"PRAGMA table_info('{selected_table}')", conn)
                    
                    st.subheader(f"Tabela: `{selected_table}`")
                    tab1, tab2 = st.tabs(["📄 Dados", "🏗️ Estrutura (Schema)"])
                    
                    with tab1:
                        df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.caption(f"Total de registros: {len(df)}")

                    with tab2:
                        st.write("Detalhes das Colunas:")
                        st.table(columns_info[['name', 'type', 'notnull', 'pk']])

                conn.close()
            else:
                st.error("Arquivo de banco de dados não encontrado dentro do zip.")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("👈 Faça o upload do arquivo para começar.")
