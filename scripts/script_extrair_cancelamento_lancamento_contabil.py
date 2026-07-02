import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Configuração de caminhos baseada no padrão solicitado
raiz_projeto = Path(__file__).resolve().parent.parent
pasta_extracoes = raiz_projeto / "extracoes"
pasta_extracoes.mkdir(exist_ok=True)


def extrair_cancelamento_lancamento_contabil():
    config = {
        'user': os.getenv('BD_USER'),
        'password': os.getenv('BD_PASSWORD'),
        'host': os.getenv('BD_HOST'),
        'database': os.getenv('BD_DATABASE'),
        'port': 3306
    }

    # Data deve ser o inicio do mes anterior ate a data atual.
    data_inicial_str = '2026-05-01'
    data_final_str = '2026-07-02'

    current_date = datetime.strptime(data_inicial_str, '%Y-%m-%d')
    end_date = datetime.strptime(data_final_str, '%Y-%m-%d')

    # Lista para acumular os dados estruturados de todos os dias
    dados_totais = []

    conexao = None
    try:
        conexao = mysql.connector.connect(**config)
        cursor = conexao.cursor(dictionary=True)

        while current_date <= end_date:
            data_consulta = current_date.strftime('%Y-%m-%d')
            print(f"Data . {data_consulta}")

            # Query de busca de cancelados idêntica à do PHP
            query = f"""
                SELECT 
                    fc.fatcte_data_cancelamento,
                    SUM(fc.fatcte_total_prestacao) AS totalCancelados, 
                    COUNT(*) AS total
                FROM corrier_fat.fat_cte fc
                WHERE fc.fatcte_data_autorizacao = '{data_consulta}' 
                  AND MONTH(fc.fatcte_data_cancelamento) IN (04, 05, 06, 07) 
                  AND YEAR(fc.fatcte_data_cancelamento) IN (2026) 
                  AND fc.fatctestat_id IN (9, 38)
                GROUP BY fc.fatcte_data_cancelamento
                ORDER BY fc.fatcte_data_cancelamento
            """

            cursor.execute(query)
            resultados = cursor.fetchall()

            if resultados:
                for row in resultados:
                    if row['total'] > 0:
                        dados_totais.append({
                            'Data Consulta (Autorização)': data_consulta,
                            'Tipo': f"{data_consulta} cancelados:",
                            'Data Cancelamento': row['fatcte_data_cancelamento'],
                            'Total Cancelados (R$)': row['totalCancelados'],
                            'Quantidade': row['total']
                        })

            current_date += timedelta(days=1)

        df = pd.DataFrame(dados_totais)

        data_atual_sistema = datetime.now().strftime('%Y-%m-%d')
        nome_arquivo = f"lancamentos_cancelados_{data_atual_sistema}.xlsx"
        caminho_arquivo = pasta_extracoes / nome_arquivo

        df.to_excel(caminho_arquivo, index=False)
        print(f"\nRelatório de lançamentos cancelados salvo em: {caminho_arquivo}")

    except Exception as e:
        print(f"Erro ao extrair relatório de lançamentos cancelados: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    extrair_cancelamento_lancamento_contabil()