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
elif pagina == "Gerador de Migration (CSV para INSERT)":  # Mantido o ID de navegação original
    st.title("📂 Gerador de Migration (CSV/JSON para INSERT)")
    st.markdown("""
    Suba um arquivo **CSV** ou o **DUMP JSON** extraído do banco para gerar um script de migração respeitando rigorosamente a tipagem dos dados.
    """)

    # Configurações na barra lateral
    nome_tabela = st.sidebar.text_input("Tabela Alvo (Schema.Tabela):", value="corrier_fat.fat_cte")
    tipo_arquivo = st.sidebar.selectbox("Tipo de Arquivo de Entrada:", ["CSV", "JSON"])
    
    separador = ";"
    if tipo_arquivo == "CSV":
        separador = st.sidebar.selectbox("Separador do CSV:", [";", ",", "\\t"], index=0, 
                                         format_func=lambda x: "Ponto e Vírgula (;)" if x == ";" else "Vírgula (,)" if x == "," else "Tabulação / TSV (\\t)")

    file_input = st.file_uploader("Suba o arquivo (CSV ou JSON)", type=["csv", "json", "txt"], key="migration_input")

    if file_input:
        try:
            if tipo_arquivo == "JSON":
                import json
                # Carrega o JSON bruto como dicionário/lista nativa do Python para não perder a tipagem
                conteudo_json = json.loads(file_input.getvalue().decode("utf-8"))
                
                # Desembrulha a query se for o formato do DBeaver
                if isinstance(conteudo_json, dict):
                    dados_reais = None
                    for chave, valor in conteudo_json.items():
                        if isinstance(valor, list):
                            dados_reais = valor
                            break
                    if dados_reais is None:
                        dados_reais = [conteudo_json]
                else:
                    dados_reais = conteudo_json
                
                # Criamos o DataFrame SEM converter tipos para preservar None/int/float originais
                df = pd.DataFrame(dados_reais)
                is_json_mode = True
            else:
                sep_atual = "\t" if separador == "\\t" else separador
                df = pd.read_csv(file_input, sep=sep_atual, engine='python', keep_default_na=False)
                is_json_mode = False
                
            st.success(f"Arquivo carregado com sucesso! Contém {len(df)} registros detectados.")
            
            if st.button("Gerar Script de Migration (INSERT)"):
                output_sql = io.StringIO()
                
                output_sql.write("-- ====================================================\n")
                output_sql.write(f"-- MIGRATION: Inserts automáticos via {tipo_arquivo} ({file_input.name})\n")
                output_sql.write("-- ====================================================\n")
                output_sql.write("BEGIN TRANSACTION;\n\n")

                colunas_tabela = ", ".join(df.columns)
                linhas_processadas = 0

                for index, row in df.iterrows():
                    valores_linha = []

                    for col, val in row.items():
                        
                        # --- REGRA CRÍTICA PARA MODO JSON (Preserva Tipagem do Objeto) ---
                        if is_json_mode:
                            # Se for null legítimo do JSON (Python None) ou se o Pandas preencheu com NaN
                            if val is None or (isinstance(val, float) and math.isnan(val)):
                                valores_linha.append("NULL")
                            # Se for String vazia "" legítima do JSON
                            elif val == '':
                                valores_linha.append("''")
                            # Se for Inteiro Puro
                            elif isinstance(val, int) and not isinstance(val, bool):
                                valores_linha.append(str(val))
                            # Se for Decimal/Float Puro
                            elif isinstance(val, float) and not isinstance(val, bool):
                                valores_linha.append(str(val))
                            # Se for Booleano Puro
                            elif isinstance(val, bool):
                                valores_linha.append(str(val).upper())
                            # Qualquer outro dado de texto (String com caracteres)
                            else:
                                val_clean = str(val).replace("'", "''")
                                valores_linha.append(f"'{val_clean}'")
                                
                        # --- REGRA PARA MODO CSV (Tudo é Lido como String via keep_default_na=False) ---
                        else:
                            val_str = str(val).strip()
                            if val_str == '' or val_str == 'NULL':
                                valores_linha.append("''")
                            elif val_str.isdigit():
                                valores_linha.append(val_str)
                            elif val_str.replace('.', '', 1).isdigit() and val_str.count('.') == 1:
                                valores_linha.append(val_str)
                            elif val_str.upper() in ['TRUE', 'FALSE']:
                                valores_linha.append(val_str.upper())
                            else:
                                val_clean = val_str.replace("'", "''")
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
                    label="⬇️ Baixar Migration (.txt)",
                    data=conteudo_sql,
                    file_name="insert_migration.txt",
                    mime="text/plain"
                )

                st.subheader("Prévia das primeiras linhas do script:")
                preview_linhas = conteudo_sql.splitlines()[:25]
                st.code("\n".join(preview_linhas), language="sql")
                    
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")