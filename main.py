from __future__ import annotations

import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from math import ceil
from typing import List, Sequence, Tuple

Matrix = List[List[int]]


@dataclass(frozen=True)
class BenchmarkResult:
    elapsed_seconds: float
    executor_used: str
    checksum: int
    sample: Tuple[Tuple[int, ...], ...]


def generate_matrix(rows: int, cols: int, seed: int) -> Matrix:
    rng = random.Random(seed)
    return [[rng.randint(1, 9) for _ in range(cols)] for _ in range(rows)]


def transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)]


def multiply_serial(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    if not matrix_a or not matrix_b:
        return []
    if len(matrix_a[0]) != len(matrix_b):
        raise ValueError("Numero de colunas de A deve ser igual ao numero de linhas de B.")

    matrix_b_t = transpose(matrix_b)
    result: Matrix = []

    for row_a in matrix_a:
        result_row: List[int] = []
        for col_b in matrix_b_t:
            result_row.append(sum(value_a * value_b for value_a, value_b in zip(row_a, col_b)))
        result.append(result_row)

    return result


def chunk_ranges(total_rows: int, chunk_size: int) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        ranges.append((start, end))
    return ranges


def multiply_row_chunk(matrix_a_rows: Sequence[Sequence[int]], matrix_b_t: Matrix) -> Matrix:
    partial_result: Matrix = []
    for row_a in matrix_a_rows:
        result_row: List[int] = []
        for col_b in matrix_b_t:
            result_row.append(sum(value_a * value_b for value_a, value_b in zip(row_a, col_b)))
        partial_result.append(result_row)
    return partial_result


def run_serial(matrix_a: Matrix, matrix_b: Matrix) -> Tuple[BenchmarkResult, Matrix]:
    started_at = time.perf_counter()
    result_matrix = multiply_serial(matrix_a, matrix_b)
    elapsed = time.perf_counter() - started_at
    return (
        BenchmarkResult(
            elapsed_seconds=elapsed,
            executor_used="serial",
            checksum=matrix_checksum(result_matrix),
            sample=matrix_sample(result_matrix),
        ),
        result_matrix,
    )


def _run_parallel_with_executor(
    executor_class,
    executor_name: str,
    matrix_a: Matrix,
    matrix_b: Matrix,
    workers: int,
) -> Tuple[BenchmarkResult, Matrix]:
    total_rows = len(matrix_a)
    chunk_size = max(1, ceil(total_rows / workers))
    row_ranges = chunk_ranges(total_rows, chunk_size)
    matrix_b_t = transpose(matrix_b)
    partial_results: List[Tuple[int, Matrix]] = []

    started_at = time.perf_counter()
    with executor_class(max_workers=workers) as executor:
        futures = {
            executor.submit(multiply_row_chunk, matrix_a[start:end], matrix_b_t): start
            for start, end in row_ranges
        }
        for future in as_completed(futures):
            partial_results.append((futures[future], future.result()))

    partial_results.sort(key=lambda item: item[0])
    result_matrix = [row for _, block in partial_results for row in block]
    elapsed = time.perf_counter() - started_at

    return (
        BenchmarkResult(
            elapsed_seconds=elapsed,
            executor_used=executor_name,
            checksum=matrix_checksum(result_matrix),
            sample=matrix_sample(result_matrix),
        ),
        result_matrix,
    )


def run_parallel(matrix_a: Matrix, matrix_b: Matrix, workers: int) -> Tuple[BenchmarkResult, Matrix]:
    try:
        return _run_parallel_with_executor(
            ProcessPoolExecutor,
            "process",
            matrix_a,
            matrix_b,
            workers,
        )
    except (PermissionError, OSError):
        return _run_parallel_with_executor(
            ThreadPoolExecutor,
            "thread-fallback",
            matrix_a,
            matrix_b,
            workers,
        )


def matrix_checksum(matrix: Matrix) -> int:
    return sum(sum(row) for row in matrix)


def matrix_sample(matrix: Matrix, sample_rows: int = 3, sample_cols: int = 3) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(row[:sample_cols]) for row in matrix[:sample_rows])


def validate_results(serial_matrix: Matrix, parallel_matrix: Matrix) -> None:
    if serial_matrix != parallel_matrix:
        raise ValueError("As matrizes resultantes da execucao serial e paralela sao diferentes.")


def speedup(serial_seconds: float, parallel_seconds: float) -> float:
    if parallel_seconds == 0:
        return float("inf")
    return serial_seconds / parallel_seconds


def efficiency(serial_seconds: float, parallel_seconds: float, workers: int) -> float:
    if workers <= 0:
        return 0.0
    return speedup(serial_seconds, parallel_seconds) / workers


def wait_for_enter(message: str) -> None:
    input(message)


def render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def horizontal(fill: str = "-") -> str:
        return "+" + "+".join(fill * (width + 2) for width in widths) + "+"

    def line(values: Sequence[str]) -> str:
        cells = [f" {value.ljust(widths[index])} " for index, value in enumerate(values)]
        return "|" + "|".join(cells) + "|"

    output = [horizontal(), line(headers), horizontal("=")]
    for row in rows:
        output.append(line(row))
        output.append(horizontal())
    return "\n".join(output)


def read_positive_int(label: str) -> int:
    raw_value = input(f"{label}: ").strip()
    value = int(raw_value)
    if value <= 0:
        raise ValueError(f"{label} deve ser maior que zero.")
    return value


def main() -> None:
    seed_a = 42
    seed_b = 99
    print("Informe as dimensoes das matrizes.")
    rows_a = read_positive_int("Qtd de Linhas Matriz A")
    cols_a = read_positive_int("Qtd de Colunas Matriz A")
    rows_b = read_positive_int("Qtd de Linhas Matriz B")
    cols_b = read_positive_int("Qtd de Colunas Matriz B")

    if cols_a != rows_b:
        print("Erro: Qtd de Colunas Matriz A deve ser igual a Qtd de Linhas Matriz B.")
        sys.exit(1)

    matrix_a = generate_matrix(rows_a, cols_a, seed_a)
    matrix_b = generate_matrix(rows_b, cols_b, seed_b)

    print("=== CONFIGURACAO DO EXPERIMENTO ===")
    print(f"Matriz A: {rows_a} x {cols_a}")
    print(f"Matriz B: {rows_b} x {cols_b}")
    print("Particionamento de Foster: divisao por blocos de linhas da matriz resultado.")
    print()

    wait_for_enter("Digite Enter para rodar serialmente...")
    serial_result, serial_matrix = run_serial(matrix_a, matrix_b)
    print()

    print("=== RESULTADOS DA EXECUCAO SERIAL ===")
    print(f"Tempo serial: {serial_result.elapsed_seconds:.6f} s")
    print(f"Checksum serial: {serial_result.checksum}")
    print("Amostra da matriz resultado:")
    for row in serial_result.sample:
        print(" ".join(str(value) for value in row))
    print()

    suggested_workers = max(2, min(4, os.cpu_count() or 2))
    workers = read_positive_int(
        f"Informe a quantidade de workers para a execucao paralela (ex.: {suggested_workers})"
    )
    parallel_result, parallel_matrix = run_parallel(matrix_a, matrix_b, workers)
    validate_results(serial_matrix, parallel_matrix)

    current_speedup = speedup(serial_result.elapsed_seconds, parallel_result.elapsed_seconds)
    current_efficiency = efficiency(
        serial_result.elapsed_seconds,
        parallel_result.elapsed_seconds,
        workers,
    )

    print()
    print("=== RESULTADOS DA EXECUCAO PARALELA ===")
    print(f"Tempo paralelo: {parallel_result.elapsed_seconds:.6f} s")
    print(f"Executor paralelo usado: {parallel_result.executor_used}")
    print(f"Checksum paralelo: {parallel_result.checksum}")
    print("Amostra da matriz resultado:")
    for row in parallel_result.sample:
        print(" ".join(str(value) for value in row))
    print()

    print("=== TABELA COMPARATIVA ===")
    print(
        render_table(
            headers=("Metrica", "Serial", "Paralela"),
            rows=(
                ("Tempo (s)", f"{serial_result.elapsed_seconds:.6f}", f"{parallel_result.elapsed_seconds:.6f}"),
                ("Executor", serial_result.executor_used, parallel_result.executor_used),
                ("Checksum", str(serial_result.checksum), str(parallel_result.checksum)),
                ("Resultados iguais", "Sim", "Sim"),
                ("Speedup", "-", f"{current_speedup:.3f}x"),
                ("Eficiencia", "-", f"{current_efficiency:.3f}"),
            ),
        )
    )
    print()

    print("=== INTERPRETACAO ===")
    print("Serial: um unico fluxo calcula todas as linhas da matriz resultado.")
    print("Paralelo: cada worker calcula um bloco independente de linhas.")
    print("Foster: particionamento por linhas, comunicacao minima e agregacao ao final.")
    if parallel_result.executor_used == "thread-fallback":
        print("Aviso: este ambiente bloqueou processos e usou threads como fallback.")


if __name__ == "__main__":
    main()
