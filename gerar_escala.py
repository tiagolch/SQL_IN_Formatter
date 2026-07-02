import os
import random
import re
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def gerar_escala_local():
    # 1. Configurações Iniciais
    arquivo_respostas = (
        "respostas.xlsx"  # Nome do seu arquivo Excel com as respostas do Form
    )

    if not os.path.exists(arquivo_respostas):
        print(
            f"❌ Erro: O arquivo '{arquivo_respostas}' não foi encontrado na mesma pasta do script."
        )
        return

    # 2. Entrada do usuário via terminal
    try:
        qtd_voluntarios = input(
            "Quantos voluntários você deseja por horário/reunião? [Padrão: 1]: "
        )
        qtd_voluntarios_por_horario = (
            int(qtd_voluntarios)
            if qtd_voluntarios.strip().isdigit()
            else 1
        )
        if qtd_voluntarios_por_horario < 1:
            qtd_voluntarios_por_horario = 1
    except ValueError:
        qtd_voluntarios_por_horario = 1

    print(
        f"⏳ Gerando escala com {qtd_voluntarios_por_horario} voluntário(s) por horário..."
    )

    # 3. Leitura dos Dados (Pandas)
    df = pd.read_excel(arquivo_respostas)
    colunas = df.columns.tolist()

    # Inicializa contagem de participações para sorteio justo
    nomes_validos = df.iloc[:, 1].dropna().unique()
    contagem_escalados = {str(nome).strip(): 0 for nome in nomes_validos}

    horarios_labels = ["9:30h", "11:30h", "17:30h"]
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Estruturas para armazenar os novos dados
    dados_escala = []
    dados_historico = []
    lista_texto_final = [
        "✨ ESCALA FINALIZADA ✨",
        "Confira abaixo sua escala e horários:",
        "",
    ]

    # 4. Lógica Principal de Sorteio
    for col_idx in range(2, len(colunas)):
        col_nome = colunas[col_idx]

        # Extrai a data de dentro dos colchetes [dd/mm/aaaa] se houver
        date_match = re.search(r"\[(.*?)\]", col_nome)
        data_evento = date_match.group(1) if date_match else col_nome

        row_escala = {"DATA": data_evento}
        lista_texto_final.append(f"📅 DATA: {data_evento}")

        for horario in horarios_labels:
            disponiveis = []
            for _, row in df.iterrows():
                nome_voluntario = str(row.iloc[1]).strip()
                celula_resposta = str(row.iloc[col_idx])

                if pd.notna(row.iloc[col_idx]) and pd.notna(row.iloc[1]):
                    opcoes_marcadas = [
                        s.strip() for s in celula_resposta.split(",")
                    ]
                    if horario in opcoes_marcadas:
                        disponiveis.append(nome_voluntario)

            escolhidos_do_horario = []

            # Sorteio múltiplo baseado na escolha do usuário
            for _ in range(qtd_voluntarios_por_horario):
                ainda_disponiveis = [
                    n for n in disponiveis if n not in escolhidos_do_horario
                ]

                if ainda_disponiveis:
                    min_participacoes = min(
                        contagem_escalados[n] for n in ainda_disponiveis
                    )
                    candidatos_prioritarios = [
                        n
                        for n in ainda_disponiveis
                        if contagem_escalados[n] == min_participacoes
                    ]

                    escolhido = random.choice(candidatos_prioritarios)
                    contagem_escalados[escolhido] += 1
                    escolhidos_do_horario.append(escolhido)

                    # CORRIGIDO: de data_generation para data_geracao
                    dados_historico.append(
                        [data_evento, horario, escolhido, data_geracao]
                    )

            # Formata a exibição visual do slot
            if escolhidos_do_horario:
                string_escolhidos = ", ".join(escolhidos_do_horario)
                if len(escolhidos_do_horario) < qtd_voluntarios_por_horario:
                    string_escolhidos += " (⚠️ VAGA INCOMPLETA)"

                row_escala[horario] = string_escolhidos
                lista_texto_final.append(
                    f"   ⏰ {horario} → {string_escolhidos}"
                )
            else:
                row_escala[horario] = "VAGO"
                lista_texto_final.append(f"   ⏰ {horario} → ⚠️ VAGO")

        dados_escala.append(row_escala)

    # 5. Criação e Formatação do Excel de Saída (OpenPyXL)
    wb = Workbook()

    # --- ABA ESCALA ---
    ws_escala = wb.active
    ws_escala.title = "Escala"
    ws_escala.views.sheetView[0].showGridLines = True

    # Título Principal
    ws_escala.merge_cells("A1:D1")
    ws_escala["A1"] = "ESCALA DE VOLUNTÁRIOS"
    ws_escala["A1"].font = Font(
        name="Calibri", size=18, bold=True, color="2E7D32"
    )
    ws_escala["A1"].alignment = Alignment(
        horizontal="center", vertical="center"
    )

    # Cabeçalho
    headers = ["DATA"] + horarios_labels
    ws_escala.append([])  # Linha vazia na linha 2
    ws_escala.append(headers)  # Linha 3

    header_fill = PatternFill(
        start_color="555555", end_color="555555", fill_type="solid"
    )
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center")

    for col_num in range(1, 5):
        cell = ws_escala.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    # Inserção de dados e formatação condicional
    thin_border = Side(style="thin", color="E0E0E0")
    border_style = Border(
        left=thin_border, right=thin_border, top=thin_border, bottom=thin_border
    )

    vago_fill = PatternFill(
        start_color="FFEBEE", end_color="FFEBEE", fill_type="solid"
    )
    vago_font = Font(name="Calibri", size=10, bold=True, color="D32F2F")
    aviso_font = Font(name="Calibri", size=10, bold=True, color="E65100")

    for i, row_data in enumerate(dados_escala):
        row_num = i + 4
        ws_escala.append(
            [
                row_data["DATA"],
                row_data["9:30h"],
                row_data["11:30h"],
                row_data["17:30h"],
            ]
        )

        bg_color = "FFFFFF" if i % 2 == 0 else "F9F9F9"
        row_fill = PatternFill(
            start_color=bg_color, end_color=bg_color, fill_type="solid"
        )

        for col_num in range(1, 5):
            cell = ws_escala.cell(row=row_num, column=col_num)
            cell.fill = row_fill
            cell.alignment = center_align
            cell.border = border_style
            cell.font = Font(name="Calibri", size=10)

            if col_num == 1:
                cell.font = Font(name="Calibri", size=10, bold=True)

            val_str = str(cell.value)
            if val_str == "VAGO":
                cell.fill = vago_fill
                cell.font = vago_font
            elif "⚠️" in val_str:
                cell.font = aviso_font

    # Ajuste dinâmico de colunas para suportar múltiplos nomes lado a lado
    ws_escala.column_dimensions["A"].width = 18
    ws_escala.column_dimensions["B"].width = 35
    ws_escala.column_dimensions["C"].width = 35
    ws_escala.column_dimensions["D"].width = 35

    ws_escala.row_dimensions[1].height = 40
    for r in range(3, ws_escala.max_row + 1):
        ws_escala.row_dimensions[r].height = 25

    # --- ABA HISTÓRICO ---
    arquivo_saida = "Escala_Gerada.xlsx"
    historico_antigo = []
    if os.path.exists(arquivo_saida):
        try:
            df_antigo = pd.read_excel(arquivo_saida, sheet_name="Historico_Geral")
            historico_antigo = df_antigo.values.tolist()
        except Exception:
            pass

    ws_hist = wb.create_sheet(title="Historico_Geral")
    ws_hist.append(
        ["DATA DO EVENTO", "HORÁRIO", "VOLUNTÁRIO", "DATA DA GERAÇÃO"]
    )

    for r_antiga in historico_antigo:
        ws_hist.append(r_antiga)
    for r_nova in dados_historico:
        ws_hist.append(r_nova)

    wb.save(arquivo_saida)

    # --- SALVA A LISTA TXT ---
    with open("Lista_Texto.txt", "w", encoding="utf-8") as txt_file:
        for linha in lista_texto_final:
            txt_file.write(linha + "\n")

    print("\n" + "=" * 50)
    print("✨ Escala e Histórico atualizados no arquivo: Escala_Gerada.xlsx")
    print("✨ Texto para copiar/enviar gerado em: Lista_Texto.txt")
    print("=" * 50)


if __name__ == "__main__":
    gerar_escala_local()