import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

raiz_projeto = Path(__file__).resolve().parent.parent
pasta_extracoes = raiz_projeto / "extracoes"
pasta_extracoes.mkdir(exist_ok=True)


def extrair_painel_contabilidade_nova():
    config = {
        'user': os.getenv('BD_USER'),
        'password': os.getenv('BD_PASSWORD'),
        'host': os.getenv('BD_HOST'),
        'database': os.getenv('BD_DATABASE'),
        'port': 3306
    }

    data_inicio_str = '2026-06-01'
    data_final_str = '2026-07-02'

    dt_orig = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    data_consulta_lotes = dt_orig.strftime('%Y-%m-01')

    current_date = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    end_date = datetime.strptime(data_final_str, '%Y-%m-%d')

    lista_df1 = []
    lista_df2 = []
    lista_df3 = []

    conexao = None
    try:
        conexao = mysql.connector.connect(**config)

        while current_date <= end_date:
            data_atual = current_date.strftime('%Y-%m-%d')

            # ============================================================
            # QUERY 1 - CONTABILIDADE NOVA POR PERÍODO
            # ============================================================
            query1 = f"""
            WITH
                Verdade_Fiscal AS (
                    SELECT
                        '{data_atual}' AS data_analise,
                        COALESCE(SUM(
                            CASE
                                WHEN p.fatcteprot_operacao IN ('emitir', 'complementar')
                                THEN c.fatcte_total_prestacao
                                ELSE 0
                            END
                        ), 0) AS SEFAZ_Autorizado,
                        COALESCE(SUM(
                            CASE
                                WHEN p.fatcteprot_operacao = 'cancelar'
                                THEN c.fatcte_total_prestacao
                                ELSE 0
                            END
                        ), 0) AS SEFAZ_Cancelado
                    FROM corrier_fat.fat_cte_protocolos p
                    INNER JOIN corrier_fat.fat_cte c USING (fatcte_id)
                    WHERE p.fatcteprot_data = '{data_atual}'
                ),
                Verdade_Contabil AS (
                    SELECT
                        COALESCE(SUM(
                            CASE
                                WHEN fatconsaplot_ctestatus = 'autorizado'
                                THEN fatconsaplot_totalprestacao
                                ELSE 0
                            END
                        ), 0) AS SAP_Autorizado,
                        COALESCE(SUM(
                            CASE
                                WHEN fatconsaplot_ctestatus = 'cancelado'
                                THEN fatconsaplot_totalprestacao
                                ELSE 0
                            END
                        ), 0) AS SAP_Cancelado
                    FROM corrier_fat.fat_contabilidade_sap_lote
                    WHERE fatconsaplot_dataconsulta = '{data_atual}'
                      AND fatconsaplotsta_id = 6
                )
            SELECT
                f.data_analise,
                f.SEFAZ_Autorizado,
                f.SEFAZ_Cancelado,
                (f.SEFAZ_Autorizado - f.SEFAZ_Cancelado) AS Saldo_Liquido_SEFAZ,
                l.SAP_Autorizado,
                l.SAP_Cancelado,
                (l.SAP_Autorizado - l.SAP_Cancelado) AS Saldo_Liquido_SAP,
                (f.SEFAZ_Autorizado - l.SAP_Autorizado) AS Gap_Autorizados,
                (f.SEFAZ_Cancelado - l.SAP_Cancelado) AS Gap_Cancelados,
                (
                    (f.SEFAZ_Autorizado - l.SAP_Autorizado) +
                    (f.SEFAZ_Cancelado - l.SAP_Cancelado)
                ) AS Total_Pendente_Homologar
            FROM Verdade_Fiscal f, Verdade_Contabil l
            """
            df1_dia = pd.read_sql(query1, conexao)
            
            if df1_dia.empty:
                df1_dia = pd.DataFrame([{
                    'data_analise': data_atual, 'SEFAZ_Autorizado': 0, 'SEFAZ_Cancelado': 0,
                    'Saldo_Liquido_SEFAZ': 0, 'SAP_Autorizado': 0, 'SAP_Cancelado': 0,
                    'Saldo_Liquido_SAP': 0, 'Gap_Autorizados': 0, 'Gap_Cancelados': 0,
                    'Total_Pendente_Homologar': 0
                }])
            lista_df1.append(df1_dia)

            # ============================================================
            # QUERY 2 - CTE SEM LOTE
            # ============================================================
            query2 = f"""
            SELECT
                e.awb,
                p.fatcte_id,
                c.fatcte_total_prestacao,
                c.fatcte_chave_acesso,
                p.fatcteprot_protocolo,
                p.fatcteprot_data,
                c.fatcte_data_autorizacao,
                c.fatctestat_id
            FROM corrier_fat.fat_cte_protocolos p
                     INNER JOIN corrier_fat.fat_cte c
                                ON p.fatcte_id = c.fatcte_id
                     join corrier.encomendas e on e.encoid = c.encoid
                     LEFT JOIN corrier_fat.fat_contabilidade_sap_lote_itens li
                               ON p.fatcte_id = li.fatcte_id
            WHERE p.fatcteprot_data = '{data_atual}'
              AND p.fatcteprot_operacao IN ('emitir', 'complementar')
              AND c.fatctestat_id NOT IN (3, 8, 9, 38)
              AND li.fatcte_id IS NULL
            """
            df2_dia = pd.read_sql(query2, conexao)
            if not df2_dia.empty:
                lista_df2.append(df2_dia)

            # ============================================================
            # QUERY 3 - CTE PENDÊNCIA DE LOTE
            # ============================================================
            query3 = f"""
            SELECT
                p.fatcte_id,
                p.fatcteprot_data,
                p.fatcteprot_operacao,
                cte.fatctestat_id
            FROM corrier_fat.fat_cte_protocolos p
            INNER JOIN corrier_fat.fat_cte cte USING (fatcte_id)
            WHERE p.fatcteprot_data = '{data_atual}'
              AND p.fatcteprot_operacao IN ('emitir', 'complementar')
              AND cte.fatctestat_id IN (3, 8, 9, 38)
              AND NOT EXISTS (
                  SELECT 1
                  FROM corrier_fat.fat_contabilidade_sap_lote_itens lti_sub
                  INNER JOIN corrier_fat.fat_contabilidade_sap_lote l_sub USING (fatconsaplot_id)
                  WHERE lti_sub.fatcte_id = p.fatcte_id
                    AND l_sub.fatconsaplot_ctestatus = 'autorizado'
                    AND l_sub.fatconsaplotsta_id <> 15
              )

            UNION

            SELECT
                p.fatcte_id,
                p.fatcteprot_data,
                p.fatcteprot_operacao,
                cte.fatctestat_id
            FROM corrier_fat.fat_cte_protocolos p
            INNER JOIN corrier_fat.fat_cte cte USING (fatcte_id)
            WHERE p.fatcteprot_data = '{data_atual}'
              AND p.fatcteprot_operacao IN ('cancelar')
              AND cte.fatctestat_id IN (9, 38)
              AND NOT EXISTS (
                  SELECT 1
                  FROM corrier_fat.fat_contabilidade_sap_lote_itens lti_sub
                  INNER JOIN corrier_fat.fat_contabilidade_sap_lote l_sub USING (fatconsaplot_id)
                  WHERE lti_sub.fatcte_id = p.fatcte_id
                    AND l_sub.fatconsaplot_ctestatus = 'cancelado'
                    AND l_sub.fatconsaplotsta_id <> 15
              )
            """
            df3_dia = pd.read_sql(query3, conexao)
            if not df3_dia.empty:
                lista_df3.append(df3_dia)

            print(f"Gerado Dia: {data_atual}")
            current_date += timedelta(days=1)

        df_final1 = pd.concat(lista_df1, ignore_index=True) if lista_df1 else pd.DataFrame()
        df_final2 = pd.concat(lista_df2, ignore_index=True) if lista_df2 else pd.DataFrame()
        df_final3 = pd.concat(lista_df3, ignore_index=True) if lista_df3 else pd.DataFrame()

        caminho_arq1 = pasta_extracoes / "contabilidade_nova_por_periodo.csv"
        df_final1.to_csv(caminho_arq1, index=False)
        print(f"Processados arquivo 1: {len(df_final1)} registros. Salvo em: {caminho_arq1}")

        caminho_arq2 = pasta_extracoes / "cte_sem_lote_por_periodo.csv"
        df_final2.to_csv(caminho_arq2, index=False)
        print(f"Processados arquivo 2: {len(df_final2)} registros. Salvo em: {caminho_arq2}")

        caminho_arq3 = pasta_extracoes / "cte_pendencia_lote_por_periodo.csv"
        df_final3.to_csv(caminho_arq3, index=False)
        print(f"Processados arquivo 3: {len(df_final3)} registros. Salvo em: {caminho_arq3}")

        # ============================================================
        # QUERY FINAL - RESUMO EM TELA (VISÃO DOS LOTES)
        # ============================================================
        query_resumo_lotes = f"""
        SELECT
            l.fatconsaplot_dataconsulta,
            l.fatconsaplotsta_id,
            s.fatconsaplotsta_nome,
            COUNT(*) AS quantidade,
            GROUP_CONCAT(DISTINCT l.fatconsaplot_id) AS lotes
        FROM corrier_fat.fat_contabilidade_sap_lote l
        JOIN corrier_fat.fat_contabilidade_sap_lote_status s
            ON s.fatconsaplotsta_id = l.fatconsaplotsta_id
        WHERE l.fatconsaplotsta_id <> 6
          AND l.fatconsaplot_dataconsulta >= '{data_consulta_lotes}'
        GROUP BY l.fatconsaplot_dataconsulta, l.fatconsaplotsta_id, s.fatconsaplotsta_nome
        ORDER BY l.fatconsaplot_dataconsulta, l.fatconsaplotsta_id
        """
        
        print("\n" + "=" * 62)
        print("VISÃO DOS LOTES EM QUE STATUS ESTÃO")
        print(f"Data base da consulta: {data_consulta_lotes}")
        print("=" * 62)

        df_resumo = pd.read_sql(query_resumo_lotes, conexao)

        if not df_resumo.empty:
            largura_data = 12
            largura_status_id = 10
            largura_status_nome = 30
            largura_qtd = 10

            header = (
                f"{'DATA'.ljust(largura_data)} | "
                f"{'STATUS_ID'.ljust(largura_status_id)} | "
                f"{'STATUS_NOME'.ljust(largura_status_nome)} | "
                f"{'QTD'.ljust(largura_qtd)} | "
                f"LOTES"
            )
            print(header)
            print("-" * 140)

            for _, row in df_resumo.iterrows():
                data_str = str(row['fatconsaplot_dataconsulta'] or '')
                status_id_str = str(row['fatconsaplotsta_id'] or '')
                status_nome_str = str(row['fatconsaplotsta_nome'] or '')
                qtd_str = str(row['quantidade'] or '')
                lotes_str = str(row['lotes'] or '')

                print(
                    f"{data_str.ljust(largura_data)} | "
                    f"{status_id_str.ljust(largura_status_id)} | "
                    f"{status_nome_str.ljust(largura_status_nome)} | "
                    f"{qtd_str.ljust(largura_qtd)} | "
                    f"{lotes_str}"
                )
        else:
            print("Nenhum lote encontrado para a data base informada.")

    except Exception as e:
        print(f"Erro ao executar o script: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()

    print(f"Fim da execução em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    extrair_painel_contabilidade_nova()