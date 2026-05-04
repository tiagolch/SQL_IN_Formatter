import streamlit as st

st.set_page_config(page_title="SQL Formatter 800", page_icon="📝")

st.title("📝 SQL IN Formatter (Quebra por Linha)")
st.markdown("Gera um único `IN (...)` com quebras de linha a cada 800 itens para melhor legibilidade.")

st.sidebar.header("Configurações")
nome_coluna = st.sidebar.text_input("Nome da Coluna:", value="ID_PRODUTO")
tipo_dado = st.sidebar.radio("Tipo de Dado:", ("Numérico", "Texto (aspas simples ')"))

uploaded_file = st.file_uploader("Carregue seu arquivo de dados (.txt)", type=["txt", "csv"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8")
    itens = [l.strip() for l in content.splitlines() if l.strip()]
    total = len(itens)
    
    st.info(f"Total de registros: {total}")

    if st.button("Gerar SQL Formatado"):
        tamanho_bloco = 800
        blocos = [itens[i:i + tamanho_bloco] for i in range(0, len(itens), tamanho_bloco)]
        
        linhas_formatadas = []
        for bloco in blocos:
            if "Texto" in tipo_dado:
                linha = ",".join(f"'{item}'" for item in bloco)
            else:
                linha = ",".join(bloco)
            linhas_formatadas.append(linha)

        corpo_sql = ",\n".join(linhas_formatadas)
        resultado_final = f"{nome_coluna} IN (\n{corpo_sql}\n)"

        st.download_button(
            label="⬇️ Baixar SQL",
            data=resultado_final,
            file_name="query_formatada.txt",
            mime="text/plain"
        )

        st.subheader("Prévia do SQL:")
        st.code(resultado_final[:5000] + ("\n..." if len(resultado_final) > 5000 else ""), language="sql")