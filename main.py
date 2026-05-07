import streamlit as st

st.set_page_config(page_title="Canivete Suíço SQL", page_icon="🛠️", layout="wide")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Selecione a Ferramenta:", ["Formatar Lista (IN)", "Gerador de Query Dinâmica"])

def ler_arquivo(uploaded_file):
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        return [l.strip() for l in content.splitlines() if l.strip()]
    return []

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

elif pagina == "Gerador de Query Dinâmica":
    st.title("⚡ Gerador de Query por Substituição")
    st.markdown("""
    Substitua valores dinâmicos na sua query. Use a tag `<id>` onde o valor da lista deve entrar.
    """)

    # Configurações da Query
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
                queries_geradas = []
                
                for item in ids:
                    valor_final = f"'{item}'" if "Texto" in tipo_id else item
                    
                    nova_query = query_modelo.replace("<id>", valor_final).strip()
                    
                    if adicionar_ponto_virgula and not nova_query.endswith(";"):
                        nova_query += ";"
                        
                    queries_geradas.append(nova_query)

                resultado_completo = "\n".join(queries_geradas)

                st.success("Processamento concluído!")
                
                st.download_button(
                    label="⬇️ Baixar Arquivo .TXT",
                    data=resultado_completo,
                    file_name="script_gerado.txt",
                    mime="text/plain"
                )
                
                st.subheader("Prévia do Script:")
                st.code("\n".join(queries_geradas[:50]), language="sql")
                if len(queries_geradas) > 50:
                    st.warning(f"Exibindo apenas as primeiras 50 de {len(queries_geradas)} queries. Baixe o arquivo para ver tudo.")
