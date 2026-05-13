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


def extrair_ralatorio_consolidado():

    config = {
        'user': os.getenv('BD_USER'),
        'password': os.getenv('BD_PASSWORD'),
        'host': os.getenv('BD_HOST'),
        'database': os.getenv('BD_DATABASE'),
        'port': 3306
    }

    query = """
        SELECT
        awb,
        encoid,
        fattar_id,
        count(1),
        fattaroper_descricao,
        sum(fattar_total) as 'Total Faturado'
        FROM
            (
            SELECT
                enc.awb,ft.encoid,ft.fattar_id, ft.fattar_total,(
                select	count(1)
                from corrier_fat.fat_tarifas ft2
                where
                    ft2.encoid = ft.encoid
                    and ft2.fattar_id > ft.fattar_id
                    and ft2.fattar_situacao = ft.fattar_situacao) as tem_tarifa_posterior,
                fto.fattaroper_descricao
            FROM
                corrier_fat.fat_tarifas ft
            inner join corrier_fat.fat_tarifas_operacoes fto on
                (fto.fattar_id = ft.fattar_id)
            inner join corrier.encomendas enc on
                (enc.encoid = ft.encoid)
            LEFT JOIN corrier_fat.fat_cte_tributos fct on
                (fct.fattar_id = ft.fattar_id)
            LEFT JOIN corrier_fat.fat_cte fc ON
                (fc.fatcte_id = fct.fatcte_id)
            WHERE
                ft.fattar_data >= '2026-04-01'
                and ft.fattarstat_id IN (30)
                and (fc.fatctestat_id <> 3
                    OR fc.fatcte_id IS NULL)
        -- 		and fto.fattaroper_descricao = ''
            HAVING
                tem_tarifa_posterior = 0) as tabela	
        GROUP BY
            fattaroper_descricao
    """

    try:
        conexao = mysql.connector.connect(**config)
        df = pd.read_sql(query, conexao)
        nome_arquivo = f"{datetime.now().strftime('%Y%m%d')}_relatorio_consolidado_dce_tarifa.xlsx"
        caminho_arquivo = pasta_extracoes / nome_arquivo
        df.to_excel(caminho_arquivo, index=False)
        print(f"Relatório consolidado salvo em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao extrair relatório consolidado: {e}")
    finally:
        if 'conexao' in locals() and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    extrair_ralatorio_consolidado()
