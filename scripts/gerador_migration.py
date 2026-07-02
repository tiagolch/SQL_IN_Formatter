# -*- coding: utf-8 -*-
import pandas as pd
import math

def gerar_migration_csv(nome_csv, nome_saida_sql):
    try:
        df = pd.read_csv(nome_csv)
    except Exception as e:
        print(f"Erro ao ler o CSV: {e}")
        return

    with open(nome_saida_sql, 'w', encoding='utf-8') as f:
        f.write("-- ====================================================\n")
        f.write(f"-- MIGRATION: Updates automáticos via CSV ({nome_csv})\n")
        f.write("-- ====================================================\n")
        f.write("BEGIN TRANSACTION;\n\n")

        linhas_processadas = 0

        for index, row in df.iterrows():
            if 'fatcli_id' not in row or pd.isna(row['fatcli_id']):
                continue
            
            fatcli_id = int(row['fatcli_id'])
            set_clauses = []

            for col, val in row.items():
                if col == 'fatcli_id':
                    continue
                
                if pd.isna(val) or val == 'NULL' or val == '':
                    set_clauses.append(f"{col} = NULL")
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    if math.isnan(val):
                        set_clauses.append(f"{col} = NULL")
                    else:
                        if isinstance(val, float) and val.is_integer():
                            set_clauses.append(f"{col} = {int(val)}")
                        else:
                            set_clauses.append(f"{col} = {val}")
                elif isinstance(val, bool):
                    set_clauses.append(f"{col} = {str(val).upper()}")
                else:
                    val_clean = str(val).replace("'", "''")
                    set_clauses.append(f"{col} = '{val_clean}'")

            if set_clauses:
                sql_update = f"UPDATE corrier_fat.fat_cte SET {', '.join(set_clauses)} WHERE fatcli_id = {fatcli_id};\n"
                f.write(sql_update)
                linhas_processadas += 1
                
        f.write("\nCOMMIT;\n")
        print(f"Sucesso! Arquivo '{nome_saida_sql}' gerado com {linhas_processadas} comandos de UPDATE.")

if __name__ == "__main__":
    gerar_migration_csv('fat_cte.csv', 'update.sql')