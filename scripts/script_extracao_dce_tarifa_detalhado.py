
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


def extrair_relatorio_erro(descricao_erro):
    config = {
        'user': os.getenv('BD_USER'),
        'password': os.getenv('BD_PASSWORD'),
        'host': os.getenv('BD_HOST'),
        'database': os.getenv('BD_DATABASE'),
        'port': 3306
    }

    query = """
    SELECT DISTINCT
        IFNULL(remg.fantasia, rem.fantasia) as `Grupo`, 
        rem.reid as `Cliente Reid`,
        rem.fantasia as `Cliente`,
        enc.encoid as `Encoid`, 
        enc.data as 'Data da Encomenda',
        rem.reid_parent,
        enc.reid,
        enc.agid,
        enc.qtyvolumes,
        enc.cep,
        cr.cep,
        IF (enc.encoid_origem IS NOT NULL AND enc.encoid_origem <> enc.encoid,'Sim','Nao') as `Peca Filha`, 
        enc.awb as `AWB`,
        enc.ultimostatid as `Ultimo Status Encomenda`,
        s.statdesc as `Descricao Status Encomenda`,
        ft.fattar_id as `TarifaID`, 
        ft.fattar_data as `Data Tarifa`, 
        ft.fattarstat_id as `Status Tarifa`,
        ft.fattar_situacao as `Situacao Tarifa`,
        fts.fattarstat_desc as `Status Tarifa Descricao`,
        fto.fattaroper_descricao as `Operacao Tarifa Descricao`,
        fto.fattaroper_tipo as `Operacao Tipo`,
        fto.fattaroper_status as `Operacao Status`,
        fct.fatctetrib_id as `TributoID`,
        fct.fatcte_id as `CTeID`,
        fc.fatcte_tipo_entrega as `Tipo Entrega`,
        fc.fatcte_data as `Data CTe`,
        fc.fatctestat_id as `Status CTe`,
        fcs.fatctestat_nome as `Status CTe Descricao`,
        fc.fatcte_total_prestacao as `Total da Prestação`,
        (select count(1) from corrier_fat.fat_tarifas ft2 where ft2.encoid = ft.encoid and ft2.fattar_id > ft.fattar_id and ft2.fattar_situacao = ft.fattar_situacao) as tem_tarifa_posterior_v1,
        (select count(1) from corrier_fat.fat_tarifas ft2 where ft2.encoid = ft.encoid and ft2.fattar_id > ft.fattar_id and ft.fattar_situacao = '') as tem_tarifa_posterior_v2,
        CASE 
            WHEN etc.enctarcon_statustarifacao = 0 THEN 'Pendente'
            WHEN etc.enctarcon_statustarifacao = 1 THEN 'Tarifado'
            WHEN etc.enctarcon_statustarifacao = 2 THEN 'Erro Tarifação'
            WHEN etc.enctarcon_statustarifacao = 3 THEN 'Tarifa Inválida'
            ELSE 'Sem Agendamento'
        END AS `Descrição Agendamento`,
        etc.enctarcon_datatarifacao AS `Data Agendamento`,
        doc.nfe_chave
    FROM corrier.encomendas enc 
    INNER JOIN corrier.remetentes rem ON (rem.reid = enc.reid)
    LEFT JOIN corrier_fat.fat_tarifas ft ON (enc.encoid = ft.encoid)
    LEFT JOIN corrier_fat.fat_tarifas_operacoes fto ON (fto.fattar_id = ft.fattar_id)
    LEFT JOIN corrier.remetentes remg ON (remg.reid = rem.reid_parent)
    LEFT JOIN corrier_fat.fat_tarifas_status fts ON (fts.fattarstat_id = ft.fattarstat_id)
    LEFT JOIN corrier_fat.fat_cte_tributos fct ON (fct.fattar_id = ft.fattar_id)
    LEFT JOIN corrier_fat.fat_cte fc ON (fc.fatcte_id = fct.fatcte_id)
    LEFT JOIN corrier_fat.fat_cte_status fcs ON (fcs.fatctestat_id = fc.fatctestat_id)
    LEFT JOIN corrier.status s ON (s.statid = enc.ultimostatid)
    LEFT JOIN corrier_fat.fat_cte_cteoriginario ec ON (ec.fatcte_id = fc.fatcte_id)
    LEFT JOIN corrier.encomendas_tarifa_controle etc ON (etc.encoid = enc.encoid)
    LEFT JOIN corrier.ceprota cr on (cr.cep = enc.cep)
    LEFT JOIN corrier.encomendas_nfe doc on (doc.encoid = enc.encoid)
    WHERE 1=1 
    AND ft.fattar_id IN (
        SELECT fattar_id FROM (
            SELECT ft.fattar_id,
            (SELECT count(1) FROM corrier_fat.fat_tarifas ft2 WHERE ft2.encoid = ft.encoid AND ft2.fattar_id > ft.fattar_id AND ft2.fattar_situacao = ft.fattar_situacao) as tem_tarifa_posterior
            FROM corrier_fat.fat_tarifas ft
            INNER JOIN corrier_fat.fat_tarifas_operacoes fto ON (fto.fattar_id = ft.fattar_id)
            INNER JOIN corrier.encomendas enc ON (enc.encoid = ft.encoid)
            LEFT JOIN corrier_fat.fat_cte_tributos fct ON (fct.fattar_id = ft.fattar_id)
            LEFT JOIN corrier_fat.fat_cte fc ON (fc.fatcte_id = fct.fatcte_id)
            WHERE ft.fattar_data >= '2026-04-01'
            AND ft.fattarstat_id IN (30)
            AND (fc.fatctestat_id <> 3 OR fc.fatcte_id IS NULL)
            AND fto.fattaroper_descricao = %s
            HAVING tem_tarifa_posterior = 0
        ) as tabela 
    )
    AND (fc.fatctestat_id NOT IN (3) OR fc.fatctestat_id IS NULL)
    GROUP BY enc.encoid
    ORDER BY fc.fatctestat_id DESC, fts.fattarstat_desc DESC;
    """

    try:
        conn = mysql.connector.connect(**config)

        print(f"Executando busca para o erro: {descricao_erro}")

        df = pd.read_sql(query, conn, params=(descricao_erro,))

        if df.empty:
            print("Nenhum dado encontrado para esta descrição.")
            return

        timestamp = datetime.now().strftime("%Y%m%d")
        descricao_erro_sanitizada = descricao_erro.replace('/', '_').replace('\\', '_').replace(':', '_').replace(
            '*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        nome_arquivo = f"{timestamp}_{descricao_erro_sanitizada}.xlsx"

        caminho_final = pasta_extracoes / nome_arquivo

        print(f"Exportando para: {caminho_final}")
        df.to_excel(caminho_final, index=False, engine='openpyxl')

        print(f"Arquivo gerado com sucesso: {nome_arquivo}")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    erro_para_buscar = ""
    extrair_relatorio_erro(erro_para_buscar)
