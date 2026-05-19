import mysql.connector
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

raiz_projeto = Path(__file__).resolve().parent.parent
pasta_extracoes = raiz_projeto / "extracoes"
pasta_extracoes.mkdir(exist_ok=True)


def extrair_relatorio_mensal():
    config = {
        'user': os.getenv('BD_USER'),
        'password': os.getenv('BD_PASSWORD'),
        'host': os.getenv('BD_HOST'),
        'database': os.getenv('BD_DATABASE'),
        'port': 3306
    }

    query ="""
        SELECT
            `ANO_MES`,
            SUM(`qtd_cte_total`) AS `qtd_cte_total`,
            SUM(`qtd_cte_autorizados`) AS `qtd_cte_autorizados`,
            SUM(`qtd_cte_nao_autorizados`) AS `qtd_cte_nao_autorizados`,
            SUM(`qtd_cte_rejeitado_gerenciais`) AS `qtd_cte_rejeitado_gerenciais`
        FROM
            (
            select
                CONCAT(LPAD(MONTH(fatcte_data), 2, '0'), '-', YEAR(fatcte_data)) AS `ANO_MES`,
                (
                select
                    count(*)
                from
                    corrier_fat.fat_cte fc1
                where
                    fc1.fatcte_data = fc.fatcte_data ) as `qtd_cte_total`,
                (
                select
                    count(*)
                from
                    corrier_fat.fat_cte fc2
                where
                    fc2.fatcte_data = fc.fatcte_data
                    AND fc2.fatctestat_id in (3, 8, 9, 29) ) as `qtd_cte_autorizados`,
                (
                select
                    count(*)
                from
                    corrier_fat.fat_cte fc3
                where
                    fc3.fatcte_data = fc.fatcte_data
                    AND fc3.fatctestat_id NOT IN (3, 8, 9, 48, 50, 29) ) as `qtd_cte_nao_autorizados`,
                (
                select
                    count(*)
                from
                    corrier_fat.fat_cte fc4
                where
                    fc4.fatcte_data = fc.fatcte_data
                    AND fc4.fatctestat_id IN (48, 50) ) as `qtd_cte_rejeitado_gerenciais`
            from
                corrier_fat.fat_cte fc
            where
                fc.fatcte_data between '2025-04-01' and CURRENT_DATE()
            group by
                fc.fatcte_data
        ) `tabela`
        GROUP BY
            `ANO_MES`
    """

    try:
        conn = mysql.connector.connect(**config)
        df = pd.read_sql(query, conn)
        conn.close()
        data_atual = datetime.now().strftime("%Y-%m-%d")
        nome_arquivo = f"{data_atual}_relatorio_mensal.xlsx"
        caminho_arquivo = pasta_extracoes / nome_arquivo
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        print(f"Relatório mensal exportado com sucesso para: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao extrair relatório mensal: {e}")
    
if __name__ == "__main__":
    extrair_relatorio_mensal()
