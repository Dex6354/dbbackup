import streamlit as st
import zipfile
import sqlite3
import os
import pandas as pd

st.set_page_config(page_title="DB Backup Explorer", layout="wide")

st.title("🎵 Music Database Explorer")
st.write("Suba seu arquivo `.backup` para visualizar as tabelas e dados.")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha o arquivo .backup", type=["backup", "zip"])

if uploaded_file is not None:
    # Criar um diretório temporário para extrair o conteúdo
    temp_dir = "temp_extracted"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            # Lista arquivos no zip para encontrar o banco de dados
            file_list = zip_ref.namelist()
            
            # Procura por 'song.db' ou 'music database'
            db_filename = next((f for f in file_list if f == "song.db" or f == "music database"), None)

            if db_filename:
                zip_ref.extract(db_filename, temp_dir)
                db_path = os.path.join(temp_dir, db_filename)
                
                # Conectar ao banco de dados SQLite
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Obter lista de tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]

                if tables:
                    st.success(f"Arquivo '{db_filename}' encontrado e carregado!")
                    
                    # Sidebar para seleção de tabela
                    selected_table = st.sidebar.selectbox("Selecione uma tabela", tables)

                    if selected_table:
                        st.header(f"Tabela: {selected_table}")
                        
                        # Ler dados usando Pandas
                        df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                        
                        # Mostrar métricas básicas
                        col1, col2 = st.columns(2)
                        col1.metric("Total de Colunas", len(df.columns))
                        col2.metric("Total de Registros", len(df))

                        # Mostrar estrutura (colunas e tipos)
                        with st.expander("Ver Estrutura das Colunas"):
                            st.write(df.dtypes.to_frame(name="Tipo de Dado"))

                        # Mostrar os dados
                        st.subheader("Itens da Tabela")
                        st.dataframe(df, use_container_width=True)
                else:
                    st.warning("O banco de dados foi encontrado, mas não contém tabelas.")
                
                conn.close()
            else:
                st.error("Não foi possível encontrar 'song.db' ou 'music database' dentro do arquivo.")

    except zipfile.BadZipFile:
        st.error("O arquivo enviado não parece ser um ZIP/Backup válido.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
    finally:
        # Limpeza simples: Remove o arquivo extraído após o uso (opcional)
        if 'db_path' in locals() and os.path.exists(db_path):
            os.remove(db_path)
else:
    st.info("Aguardando upload...")
