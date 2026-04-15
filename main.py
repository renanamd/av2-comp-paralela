from __future__ import annotations

import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from math import ceil
from typing import List, Sequence, Tuple

Matriz = List[List[int]]


@dataclass(frozen=True)
class ResultadoBenchmark:
    tempo_decorrido_segundos: float
    executor_utilizado: str
    amostra: Tuple[Tuple[int, ...], ...]


def gerar_matriz(linhas: int, colunas: int, semente: int) -> Matriz:
    gerador = random.Random(semente)
    return [[gerador.randint(1, 9) for _ in range(colunas)] for _ in range(linhas)]


def transpor(matriz: Matriz) -> Matriz:
    return [list(coluna) for coluna in zip(*matriz)]


def multiplicar_serial(matriz_a: Matriz, matriz_b: Matriz) -> Matriz:
    if not matriz_a or not matriz_b:
        return []
    if len(matriz_a[0]) != len(matriz_b):
        raise ValueError("Numero de colunas de A deve ser igual ao numero de linhas de B.")

    matriz_b_transposta = transpor(matriz_b)
    resultado: Matriz = []

    for linha_a in matriz_a:
        linha_resultado: List[int] = []
        for coluna_b in matriz_b_transposta:
            linha_resultado.append(sum(valor_a * valor_b for valor_a, valor_b in zip(linha_a, coluna_b)))
        resultado.append(linha_resultado)

    return resultado


def intervalos_blocos(total_linhas: int, tamanho_bloco: int) -> List[Tuple[int, int]]:
    intervalos: List[Tuple[int, int]] = []
    for inicio in range(0, total_linhas, tamanho_bloco):
        fim = min(inicio + tamanho_bloco, total_linhas)
        intervalos.append((inicio, fim))
    return intervalos


def multiplicar_bloco_linhas(linhas_matriz_a: Sequence[Sequence[int]], matriz_b_transposta: Matriz) -> Matriz:
    resultado_parcial: Matriz = []
    for linha_a in linhas_matriz_a:
        linha_resultado: List[int] = []
        for coluna_b in matriz_b_transposta:
            linha_resultado.append(sum(valor_a * valor_b for valor_a, valor_b in zip(linha_a, coluna_b)))
        resultado_parcial.append(linha_resultado)
    return resultado_parcial


def executar_serial(matriz_a: Matriz, matriz_b: Matriz) -> Tuple[ResultadoBenchmark, Matriz]:
    inicio = time.perf_counter()
    matriz_resultado = multiplicar_serial(matriz_a, matriz_b)
    tempo_decorrido = time.perf_counter() - inicio
    return (
        ResultadoBenchmark(
            tempo_decorrido_segundos=tempo_decorrido,
            executor_utilizado="serial",
            amostra=amostra_matriz(matriz_resultado),
        ),
        matriz_resultado,
    )


def executar_paralelo_processos(
    matriz_a: Matriz, matriz_b: Matriz, workers: int
) -> Tuple[ResultadoBenchmark, Matriz]:
    return _executar_paralelo_com_executor(
        ProcessPoolExecutor,
        "process",
        matriz_a,
        matriz_b,
        workers,
    )


def executar_paralelo_threads(
    matriz_a: Matriz, matriz_b: Matriz, workers: int
) -> Tuple[ResultadoBenchmark, Matriz]:
    return _executar_paralelo_com_executor(
        ThreadPoolExecutor,
        "thread",
        matriz_a,
        matriz_b,
        workers,
    )


def _executar_paralelo_com_executor(
    classe_executor,
    nome_executor: str,
    matriz_a: Matriz,
    matriz_b: Matriz,
    workers: int,
) -> Tuple[ResultadoBenchmark, Matriz]:
    total_linhas = len(matriz_a)
    tamanho_bloco = max(1, ceil(total_linhas / workers))
    intervalos_linhas = intervalos_blocos(total_linhas, tamanho_bloco)
    matriz_b_transposta = transpor(matriz_b)
    resultados_parciais: List[Tuple[int, Matriz]] = []

    inicio = time.perf_counter()
    with classe_executor(max_workers=workers) as executor:
        futures = {
            executor.submit(multiplicar_bloco_linhas, matriz_a[inicio_bloco:fim_bloco], matriz_b_transposta): inicio_bloco
            for inicio_bloco, fim_bloco in intervalos_linhas
        }
        for future in as_completed(futures):
            resultados_parciais.append((futures[future], future.result()))

    resultados_parciais.sort(key=lambda item: item[0])
    matriz_resultado = [linha for _, bloco in resultados_parciais for linha in bloco]
    tempo_decorrido = time.perf_counter() - inicio

    return (
        ResultadoBenchmark(
            tempo_decorrido_segundos=tempo_decorrido,
            executor_utilizado=nome_executor,
            amostra=amostra_matriz(matriz_resultado),
        ),
        matriz_resultado,
    )

def amostra_matriz(matriz: Matriz, linhas_amostra: int = 3, colunas_amostra: int = 3) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(linha[:colunas_amostra]) for linha in matriz[:linhas_amostra])


def validar_resultados(matriz_serial: Matriz, matriz_paralela: Matriz) -> None:
    if matriz_serial != matriz_paralela:
        raise ValueError("As matrizes resultantes da execucao serial e paralela sao diferentes.")


def calcular_speedup(tempo_serial: float, tempo_paralelo: float) -> float:
    if tempo_paralelo == 0:
        return float("inf")
    return tempo_serial / tempo_paralelo


def calcular_eficiencia(tempo_serial: float, tempo_paralelo: float, workers: int) -> float:
    if workers <= 0:
        return 0.0
    return calcular_speedup(tempo_serial, tempo_paralelo) / workers


def esperar_enter(mensagem: str) -> None:
    input(mensagem)


def renderizar_tabela(cabecalhos: Sequence[str], linhas: Sequence[Sequence[str]]) -> str:
    larguras = [len(cabecalho) for cabecalho in cabecalhos]
    for linha in linhas:
        for indice, celula in enumerate(linha):
            larguras[indice] = max(larguras[indice], len(celula))

    def horizontal(preenchimento: str = "-") -> str:
        return "+" + "+".join(preenchimento * (largura + 2) for largura in larguras) + "+"

    def linha_tabela(valores: Sequence[str]) -> str:
        celulas = [f" {valor.ljust(larguras[indice])} " for indice, valor in enumerate(valores)]
        return "|" + "|".join(celulas) + "|"

    saida = [horizontal(), linha_tabela(cabecalhos), horizontal("=")]
    for linha in linhas:
        saida.append(linha_tabela(linha))
        saida.append(horizontal())
    return "\n".join(saida)


def ler_inteiro_positivo(rotulo: str) -> int:
    valor_bruto = input(f"{rotulo}: ").strip()
    valor = int(valor_bruto)
    if valor <= 0:
        raise ValueError(f"{rotulo} deve ser maior que zero.")
    return valor


def ler_tipo_execucao() -> str:
    print()
    print("Escolha o tipo de execucao:")
    print("1 - Serial")
    print("2 - Paralela com threads")
    print("3 - Paralela com processos")

    opcao = input("Opcao: ").strip()
    tipos_execucao = {
        "1": "serial",
        "2": "thread",
        "3": "process",
    }

    if opcao not in tipos_execucao:
        raise ValueError("Opcao de execucao invalida.")

    return tipos_execucao[opcao]


def descrever_tipo_execucao(tipo_execucao: str) -> str:
    descricoes = {
        "serial": "serial",
        "thread": "paralela com threads",
        "process": "paralela com processos",
    }
    return descricoes[tipo_execucao]


def main() -> None:
    semente_a = 42
    semente_b = 99
    print("Informe as dimensoes das matrizes.")
    linhas_a = ler_inteiro_positivo("Qtd de Linhas Matriz A")
    colunas_a = ler_inteiro_positivo("Qtd de Colunas Matriz A")
    linhas_b = ler_inteiro_positivo("Qtd de Linhas Matriz B")
    colunas_b = ler_inteiro_positivo("Qtd de Colunas Matriz B")

    if colunas_a != linhas_b:
        print("Erro: Qtd de Colunas Matriz A deve ser igual a Qtd de Linhas Matriz B.")
        sys.exit(1)

    tipo_execucao = ler_tipo_execucao()
    matriz_a = gerar_matriz(linhas_a, colunas_a, semente_a)
    matriz_b = gerar_matriz(linhas_b, colunas_b, semente_b)

    print("=== CONFIGURACAO DO EXPERIMENTO ===")
    print(f"Matriz A: {linhas_a} x {colunas_a}")
    print(f"Matriz B: {linhas_b} x {colunas_b}")
    print("Particionamento de Foster: divisao por blocos de linhas da matriz resultado.")
    print(f"Execucao escolhida: {descrever_tipo_execucao(tipo_execucao)}")
    print()

    workers = 1
    esperar_enter(f"Digite Enter para rodar a execucao {descrever_tipo_execucao(tipo_execucao)}...")

    if tipo_execucao == "serial":
        resultado_execucao, matriz_resultado = executar_serial(matriz_a, matriz_b)
    else:
        workers_sugeridos = max(2, min(4, os.cpu_count() or 2))
        workers = ler_inteiro_positivo(
            f"Informe a quantidade de workers para a execucao {descrever_tipo_execucao(tipo_execucao)} (ex.: {workers_sugeridos})"
        )
        if tipo_execucao == "thread":
            resultado_execucao, matriz_resultado = executar_paralelo_threads(matriz_a, matriz_b, workers)
        else:
            resultado_execucao, matriz_resultado = executar_paralelo_processos(matriz_a, matriz_b, workers)
    print()

    print("=== RESULTADOS DA EXECUCAO ===")
    print(f"Tempo de execucao: {resultado_execucao.tempo_decorrido_segundos:.6f} s")
    print(f"Executor usado: {resultado_execucao.executor_utilizado}")
    print("Amostra da matriz resultado:")
    for linha in resultado_execucao.amostra:
        print(" ".join(str(valor) for valor in linha))
    print()

    print("=== INTERPRETACAO ===")
    if tipo_execucao == "serial":
        print("Serial: um unico fluxo calcula todas as linhas da matriz resultado.")
    else:
        print("Paralelo: cada worker calcula um bloco independente de linhas.")
        print(f"Workers utilizados: {workers}")
        print("Foster: particionamento por linhas, comunicacao minima e agregacao ao final.")


if __name__ == "__main__":
    main()
