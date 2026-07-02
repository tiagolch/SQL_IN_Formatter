import os
from datetime import datetime
from pathlib import Path
import zipfile
import mysql.connector
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

raiz_projeto = Path(__file__).resolve().parent.parent
pasta_extracoes = raiz_projeto / "extracoes"
pasta_extracoes.mkdir(exist_ok=True)


def extrair_relatorio_cte_faturas_alta_performance():
    config = {
        "user": os.getenv("BD_USER"),
        "password": os.getenv("BD_PASSWORD"),
        "host": os.getenv("BD_HOST"),
        "database": os.getenv("BD_DATABASE"),
        "port": 3306,
    }

    faturas_alvo = (
        'CT 1017592','CT 1017588','CT 1017585','CT 1017577','CT 1017573','CT 1017569','CT 1017568','CT 1017562','CT 1017536','CT 1017535','CT 1017317','CT 1017276','CT 1017263','CT 1017157','CT 1016972','CT 1016962','CT 1016956','CT 1016951','CT 1016941','CT 1016887','CT 1016785','CT 1016760','CT 1016759','CT 1016758','CT 1016718','CT 1016717','CT 1016698','CT 1016697','CT 1016696','CT 1016671','CT 1016670','CT 1016668','CT 1016667','CT 1016666','CT 1016664','CT 1016663','CT 1016563','CT 1016562','CT 1016561','CT 1016560','CT 1016559','CT 1016558','CT 1016557','CT 1016556','CT 1016555','CT 1016553','CT 1016552','CT 1016551','CT 1016549','CT 1016512','CT 1016509','CT 1016503','CT 1016497','CT 1016472','CT 1016350','CT 1016347','CT 1016344','CT 1016340','CT 1016336','CT 1016334','CT 1016331','CT 1016275','CT 1016126','CT 1016125','CT 1016123','CT 1016122','CT 1016121','CT 1016120','CT 1016119','CT 1016116','CT 1016113','CT 1016112','CT 1016109','CT 1016084','CT 1016082','CT 1016081','CT 1016079','CT 1016077','CT 1016075','CT 1016073','CT 1016071','CT 1016069','CT 1016067','CT 1016066','CT 1016065','CT 1016064','CT 1016063','CT 1016005','CT 1015981','CT 1015950','CT 1015949','CT 1015948','CT 1015947','CT 1015943','CT 1015766','CT 1015764','CT 1015668','CT 1015665','CT 1015612','CT 1015580','CT 1015542','CT 1015510','CT 1015508','CT 1015478','CT 1015477','CT 1015476','CT 1015475','CT 1015474','CT 1015473','CT 1015472','CT 1015471','CT 1015470','CT 1015469','CT 1015469','CT 1015468','CT 1015467','CT 1015466','CT 1015465','CT 1015439','CT 1015438','CT 1015437','CT 1015436','CT 1015394','CT 1015393','CT 1015392','CT 1015301','CT 1015294','CT 1015293','CT 1015290','CT 1015286','CT 1015285','CT 1015284','CT 1015281','CT 1015276','CT 1015253','CT 1015252','CT 1015251','CT 1015211','CT 1015210','CT 1015173','CT 1015172','CT 1015021','CT 1015000','CT 1014989','CT 1014897','CT 1014854','CT 1014848','CT 1014847','CT 1014846','CT 1014845','CT 1014844','CT 1014843','CT 1014684','CT 1014618','CT 1014553','CT 1014552','CT 1014551','CT 1014516','CT 1014515','CT 1014514','CT 1014513','CT 1014512','CT 1014511','CT 1014510','CT 1014509','CT 1014508','CT 1014507','CT 1014506','CT 1014505','CT 1014504','CT 1014503','CT 1014502','CT 1014501','CT 1014500','CT 1014499','CT 1014498','CT 1014497','CT 1014496','CT 1014495','CT 1014494','CT 1014493','CT 1014492','CT 1014473','CT 1014369','CT 1014321','CT 1014320','CT 1014319','CT 1014318','CT 1014317','CT 1014284','CTSP 1014219','CT 1014079','CT 1014077','CT 1013970','CT 1013969','CT 1013859','CT 1013858','CT 1013795','CT 1013764','CT 1013700','CT 1013699','CT 1013698','CT 1013697','CT 1013696','CT 1013660','CT 1013659','CT 1013658','CT 1013657','CT 1013656','CT 1013655','CT 1013640','CT 1013614','CT 1013613','CT 1013610','CT 1013603','CT 1013599','CT 1013565','CT 1013543','CT 1013542','CT 1013537','CT 1013365','CT 1013360','CT 1013357','CT 1013308','CT 1013307','CT 1013216','CT 1013209','CT 1013204','CT 1013109','CT 1013107','CT 1013106','CT 1013032','CT 1012943','CT 1012937','CT 1012928','CT 1012926','CT 1012925','CT 1012923','CT 1012922','CT 1012920','CT 1012918','CT 1012896','CT 1012895','CT 1012894','CT 1012893','CT 1012892','CT 1012796','CT 1012791','CT 1012595','CT 1012593','CT 1012589','CT 1012485','CT 1012484','CT 1012400','CT 1012394','CT 1012393','CT 1012329','CT 1012326','CT 1012321','CT 1012316','CT 1012226','CT 1012225','CT 1012191','CT 1012170','CT 1012169','CT 1012167','CT 1012166','CT 1012164','CT 1011960','CT 1011873','CT 1011872','CT 1011801','CT 1011686','CT 1011651','CT 1011547','CT 1011546','CT 1011490','CT 1011489','CT 1011487','CT 1011486','CT 1011485','CT 1011419','CT 1011413','CT 1011407'
                    )

    limite_por_arquivo = 950000
    tamanho_bloco_leitura = 20000
    nome_base_arquivo = "Relatorio_CTes_269_faturas_"
    indice_arquivo = 1

    qtd_total_processada = 0
    qtd_no_arquivo_atual = 0

    caminho_arquivo_atual = None
    primeiro_bloco_do_arquivo = True
    arquivos_gerados = [] 

    def preparar_novo_arquivo():
        nonlocal indice_arquivo, qtd_no_arquivo_atual, primeiro_bloco_do_arquivo, caminho_arquivo_atual
        nome_arquivo = (
            f"{nome_base_arquivo}_parte_{str(indice_arquivo).zfill(3)}.csv"
        )
        caminho_arquivo_atual = pasta_extracoes / nome_arquivo
        print(f"Gerando arquivo: {caminho_arquivo_atual}")

        if caminho_arquivo_atual.exists():
            caminho_arquivo_atual.unlink()

        arquivos_gerados.append(caminho_arquivo_atual)
        indice_arquivo += 1
        qtd_no_arquivo_atual = 0
        primeiro_bloco_do_arquivo = True

    try:
        conn = mysql.connector.connect(**config)

        print(f"Buscando IDs para as faturas: {faturas_alvo}...")
        clausula_in = (
            str(faturas_alvo)
            if len(faturas_alvo) > 1
            else f"('{faturas_alvo[0]}')"
        )
        query_ids = f"SELECT DISTINCT `fatcli_id` FROM `corrier_fat`.`fat_faturas_clientes` WHERE `fatcli_numero` IN {clausula_in};"

        df_ids = pd.read_sql(query_ids, conn)
        fatcliIds = df_ids["fatcli_id"].tolist()

        if not fatcliIds:
            print("Aviso: Nenhum fatcli_id foi encontrado. Encerrando.")
            conn.close()
            return

        print(f"Encontrados {len(fatcliIds)} IDs para processar: {fatcliIds}")

        preparar_novo_arquivo()

        cursor = conn.cursor(dictionary=True, buffered=False)

        for fatcliId in fatcliIds:
            print(f"Iniciando streaming de dados para fatcli_id: {fatcliId}")

            query = f"""
            SELECT `fatctetrib_frete_peso_volume`, `fatctetrib_frete_valor`, `fct`.`reid`, `fc`.`fatcte_id`,
                   `fc`.`fatcte_data_autorizacao`, `fc`.`fatcte_data`, `fc`.`fatcte_cte`, `fatcte_serie`,
                   `fatcte_chave_acesso`, `fc`.`fatctestat_id`, `e`.`awb`, `e`.`nfiscal`, `e`.`nome`,
                   `e`.`endereco`, `fattar_rota`, `e`.`tipo_entrega`, `fatctetrib_agendamento`, `e`.`pedido`,
                   `e`.`nfiscalvalor`, `e`.`cpf`, `fc`.`fatcte_remetente_nome`, `fc`.`fatcte_acao_documento`,
                   `e`.`cod_barra`, `e`.`cidade`, `ft`.`fattar_data`, `fc`.`fatcte_aliquota`, `fatcte_tipo_entrega`,
                   `e`.`cep`, `e`.`data`, `f`.`fatcli_numero`,
                   IF(`f`.`fatcli_numero_abril` IS NULL OR `f`.`fatcli_numero_abril` = '', `f`.`fatcli_numero_sequencial_sap`, `f`.`fatcli_numero_abril`) AS `numero_fatura`,
                   `ft`.`fattar_peso` AS `peso`, `fct`.`fatctetrib_tx_ad_frete`, `e`.`nfiscalserie`, `fc`.`fatcte_isencao_icms`,
                   `fattar_situacao`, `ft`.`fattar_gris`, `fattar_advalorem`, `fattar_cod`, `fattar_goback_rma`,
                   `fattar_frete`, `fattar_postagem`, `fattar_agendamento`, `fattar_tx_ad_frete`, `fattar_tx_ad_servico`,
                   `fattar_total`, `fatctetrib_valor_tributos`, `fatctetrib_total`, `fatcte_total_prestacao`,
                   `e`.`encoid_origem`, `fc`.`fatcte_isencao_icms`, `fcs`.`fatctestat_nome`,
                   IFNULL(`fgi`.`fatgeoit_uf_especial`, `cr`.`uf`) AS `estado`, `tm`.`nom_mercado` AS `tipo_operacao`,
                   `e`.`condfrete`, `ftd`.`desconto` AS `desconto_frete`
            FROM `corrier_fat`.`fat_cte` `fc`
                     INNER JOIN `corrier_fat`.`fat_cte_tributos` `fct` ON (`fc`.`fatcte_id` = `fct`.`fatcte_id`)
                     INNER JOIN `corrier_fat`.`fat_cte_status` `fcs` ON (`fcs`.`fatctestat_id` = `fc`.`fatctestat_id`)
                     INNER JOIN `corrier_fat`.`fat_tarifas` `ft` ON (`fct`.`fattar_id` = `ft`.`fattar_id`)
                     INNER JOIN `corrier`.`encomendas` `e` ON (`ft`.`encoid` = `e`.`encoid`)
                     INNER JOIN `corrier_new`.`tb_contrato_reid` `r` ON (`r`.`reid` = `fc`.`reid`)
                     INNER JOIN `corrier_new`.`tb_contrato` `tc` ON (`r`.`pk_num_contrato` = `tc`.`pk_num_contrato`)
                     INNER JOIN `corrier_fat`.`fat_faturas_clientes` `f` ON (`fc`.`fatcli_id` = `f`.`fatcli_id`)
                     LEFT JOIN `corrier_new`.`tb_mercado` `tm` ON (`tm`.`pk_num_mercado` = `tc`.`num_mercado`)
                     LEFT JOIN `corrier`.`ceprota` `cr` ON (`e`.`cep` = `cr`.`cep`)
                     LEFT JOIN `corrier_fat`.`fat_configuracoes` `ftc` ON (`ft`.`fatconf_id` = `ftc`.`fatconf_id`)
                     LEFT JOIN `corrier_fat`.`fat_geografia_itens` `fgi`
                            ON (`ftc`.`fatgeo_id` = `fgi`.`fatgeo_id` AND `cr`.`uf` = `fgi`.`fatgeoit_uf` AND `cr`.`municipio_ibge` = `fgi`.`fatgeoit_cidade_ibge`)
                     LEFT JOIN `corrier_fat`.`fat_tarifas_desconto` `ftd` ON (`ft`.`fattar_id` = `ftd`.`fattar_id`)
            WHERE `fc`.`fatcli_id` = {fatcliId}
              AND `fc`.`fatctestat_id` IN (3, 8, 7, 9, 38)
            """

            cursor.execute(query)

            qtd_fatcli = 0

            while True:
                linhas = cursor.fetchmany(tamanho_bloco_leitura)
                if not linhas:
                    break

                qtd_linhas_bloco = len(linhas)
                qtd_fatcli += qtd_linhas_bloco
                qtd_total_processada += qtd_linhas_bloco

                df_bloco = pd.DataFrame(linhas)

                if qtd_no_arquivo_atual + qtd_linhas_bloco > limite_por_arquivo:
                    linhas_restantes = limite_por_arquivo - qtd_no_arquivo_atual

                    if linhas_restantes > 0:
                        df_resto = df_bloco.iloc[:linhas_restantes]
                        df_resto.to_csv(
                            caminho_arquivo_atual,
                            mode="a",
                            index=False,
                            sep=";",
                            header=primeiro_bloco_do_arquivo,
                            encoding="utf-8",
                        )

                    df_bloco = df_bloco.iloc[linhas_restantes:]
                    preparar_novo_arquivo()

                df_bloco.to_csv(
                    caminho_arquivo_atual,
                    mode="a",
                    index=False,
                    sep=";",
                    header=primeiro_bloco_do_arquivo,
                    encoding="utf-8",
                )

                primeiro_bloco_do_arquivo = False
                qtd_no_arquivo_atual += len(df_bloco)

            print(
                f"-> Finalizado fatcli_id {fatcliId}: {qtd_fatcli} registros processados."
            )

        cursor.close()
        conn.close()

        print(
            f"\n[SUCESSO] Processados {qtd_total_processada} registros no total."
        )

        if arquivos_gerados and qtd_total_processada > 0:
            data_atual = datetime.now().strftime("%Y-%m-%d")
            nome_zip = (
                f"Relatorio_Faturas_Geradas_{data_atual}.zip"
            )
            caminho_zip = pasta_extracoes / nome_zip

            print(f"\nIniciando compactação dos arquivos em: {caminho_zip}")

            with zipfile.ZipFile(
                caminho_zip, "w", zipfile.ZIP_DEFLATED
            ) as zipf:
                for arquivo in arquivos_gerados:
                    if arquivo.exists():
                        zipf.write(arquivo, arcname=arquivo.name)
                        arquivo.unlink()

            print(f"Compactação concluída com sucesso!")
        else:
            print("\nNenhum arquivo foi gerado para compactação.")

    except Exception as e:
        print(f"Erro crítico ao executar o script: {e}")

    print(f"Fim da execução em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    extrair_relatorio_cte_faturas_alta_performance()