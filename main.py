# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="Canivete Suíço SQL", page_icon="🛠️", layout="wide")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Selecione a Ferramenta:", 
    ["Formatar Lista (IN)", "Gerador de Query Dinâmica", "Gerador de Migration (CSV para INSERT)"]
)

def ler_arquivo(uploaded_file):
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        return [l.strip() for l in content.splitlines() if l.strip()]
    return []

# ==========================================
# FERRAMENTA 1: FORMATAR LISTA (IN)
# ==========================================
if pagina == "Formatar Lista (IN)":
    st.title("🎯 Formatar Lista para SQL IN")
    st.markdown("Transforma listas em blocos de 1000 com quebras de linha dentro de um único `IN (...)`.")

    nome_coluna = st.sidebar.text_input("Nome da Coluna:", value="ID_PRODUTO")
    tipo_dado = st.sidebar.radio("Tipo de Dado:", ("Numérico", "Texto (aspas simples ')"))
    
    file = st.file_uploader("Suba o arquivo de IDs", type=["txt", "csv"], key="lista_in")
    ids = ler_arquivo(file)

    if ids:
        st.success(f"{len(ids)} IDs carregados.")
        if st.button("Gerar SQL IN"):
            tamanho_bloco = 1000
            blocos = [ids[i:i + tamanho_bloco] for i in range(0, len(ids), tamanho_bloco)]
            
            linhas_formatadas = []
            for b in blocos:
                item_fmt = ",".join([f"'{x}'" if "Texto" in tipo_dado else x for x in b])
                linhas_formatadas.append(item_fmt)
            
            resultado = f"{nome_coluna} IN (\n" + ",\n".join(linhas_formatadas) + "\n)"
            
            st.download_button("⬇️ Baixar SQL IN", data=resultado, file_name="lista_in.txt")
            st.code(resultado[:2000] + "...", language="sql")

# ==========================================
# FERRAMENTA 2: GERADOR DE QUERY DINÂMICA
# ==========================================
elif pagina == "Gerador de Query Dinâmica":
    st.title("⚡ Gerador de Query por Substituição")
    st.markdown("""
    Substitua valores dinâmicos na sua query. Use a tag `<id>` onde o valor da lista deve entrar.
    """)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        query_modelo = st.text_area("Modelo da Query:", value="UPDATE tabela SET coluna = 'processado' WHERE id_referencia = <id>;", height=150)
    
    with col2:
        st.write("### Opções")
        tipo_id = st.radio("Como tratar o <id>?", ("Número (sem aspas)", "Texto (com aspas '')"))
        adicionar_ponto_virgula = st.checkbox("Garantir ';' ao final de cada linha", value=True)

    file = st.file_uploader("Suba o arquivo de IDs", type=["txt", "csv"], key="query_ids")
    ids = ler_arquivo(file)

    if ids:
        st.info(f"{len(ids)} IDs carregados para processamento.")
        
        if st.button("Gerar Script SQL Completo"):
            if "<id>" not in query_modelo:
                st.error("Erro: A tag <id> não foi encontrada no seu modelo de query!")
            else:
                queries_generadas = []
                
                for item in ids:
                    valor_final = f"'{item}'" if "Texto" in tipo_id else item
                    nova_query = query_modelo.replace("<id>", valor_final).strip()
                    
                    if adicionar_ponto_virgula and not nova_query.endswith(";"):
                        nova_query += ";"
                        
                    queries_generadas.append(nova_query)

                resultado_completo = "\n".join(queries_generadas)

                st.success("Processamento concluído!")
                
                st.download_button(
                    label="⬇️ Baixar Arquivo .TXT",
                    data=resultado_completo,
                    file_name="script_gerado.txt",
                    mime="text/plain"
                )
                
                st.subheader("Prévia do Script:")
                st.code("\n".join(queries_generadas[:50]), language="sql")
                if len(queries_generadas) > 50:
                    st.warning(f"Exibindo apenas as primeiras 50 de {len(queries_generadas)} queries. Baixe o arquivo para ver tudo.")

# ==========================================
# FERRAMENTA 3: GERADOR DE MIGRATION (INSERT)
# ==========================================
elif pagina == "Gerador de Migration (CSV para INSERT)":
    st.title("📂 Gerador de Migration (CSV para INSERT)")
    st.markdown("""
    Suba o arquivo CSV extraído do banco para gerar um script de migração contendo os comandos de `INSERT` estruturados linha por linha.
    """)

    nome_tabela = st.sidebar.text_input("Tabela Alvo (Schema.Tabela):", value="corrier_fat.fat_cte")

    file_csv = st.file_uploader("Suba o arquivo CSV", type=["csv"], key="migration_csv")

    if file_csv:
        try:
            df = pd.read_csv(file_csv)
            st.success(f"CSV carregado com sucesso! Contém {len(df)} registros detectados.")
            
            if st.button("Gerar Script de Migration (INSERT)"):
                output_sql = io.StringIO()
                
                output_sql.write("-- ====================================================\n")
                output_sql.write(f"-- MIGRATION: Inserts automáticos via CSV ({file_csv.name})\n")
                output_sql.write("-- ====================================================\n")
                output_sql.write("BEGIN TRANSACTION;\n\n")

                # Obtém a lista de todas as colunas do cabeçalho do CSV para o INSERT
                colunas_tabela = ", ".join(df.columns)
                linhas_processadas = 0

                for index, row in df.iterrows():
                    valores_linha = []

                    for col, val in row.items():
                        # Trata valores nulos ou vazios
                        if pd.isna(val) or val == 'NULL' or val == '':
                            valores_linha.append("NULL")
                        # Trata valores numéricos
                        elif isinstance(val, (int, float)) and not isinstance(val, bool):
                            if math.isnan(val):
                                valores_linha.append("NULL")
                            else:
                                if isinstance(val, float) and val.is_integer():
                                    valores_linha.append(str(int(val)))
                                else:
                                    valores_linha.append(str(val))
                        # Trata booleanos
                        elif isinstance(val, bool):
                            valores_linha.append(str(val).upper())
                        # Trata strings, textos e datas
                        else:
                            val_clean = str(val).replace("'", "''")
                            valores_linha.append(f"'{val_clean}'")

                    if valores_linha:
                        valores_formatados = ", ".join(valores_linha)
                        sql_insert = f"INSERT INTO {nome_tabela} ({colunas_tabela}) VALUES ({valores_formatados});\n"
                        output_sql.write(sql_insert)
                        linhas_processadas += 1
                        
                output_sql.write("\nCOMMIT;\n")
                conteudo_sql = output_sql.getvalue()

                st.success(f"Sucesso! Gerados {linhas_processadas} comandos de INSERT.")
                
                st.download_button(
                    label="⬇️ Baixar Migration (.SQL)",
                    data=conteudo_sql,
                    file_name="insert_migration.txt",
                    mime="text/plain"
                )

                st.subheader("Prévia das primeiras linhas do script:")
                preview_linhas = conteudo_sql.splitlines()[:25]
                st.code("\n".join(preview_linhas), language="sql")
                    
        except Exception as e:
            st.error(f"Erro ao processar o arquivo CSV: {e}")