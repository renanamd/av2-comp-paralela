# AV2 - Computacao Paralela e Concorrente

Implementacao em Python para comparar multiplicacao de matrizes em execucao serial e paralela, usando a metodologia de Foster.

## Como executar

```powershell
python main.py
```

Ao executar, o programa pede no terminal:

```powershell
python main.py
```

Entradas solicitadas:

- `Qtd de Linhas Matriz A`
- `Qtd de Colunas Matriz A`
- `Qtd de Linhas Matriz B`
- `Qtd de Colunas Matriz B`
- `Quantidade de workers` antes da execucao paralela

Se `Colunas A != Linhas B`, o programa exibe erro e encerra.

Fluxo da demonstracao:

- o usuario informa as dimensoes;
- pressiona `Enter` para executar a versao serial;
- visualiza os resultados da execucao serial;
- informa a quantidade de `workers` para a execucao paralela;
- visualiza os resultados paralelos e a tabela comparativa final.

## O que o programa faz

- Gera duas matrizes com valores aleatorios controlados por semente.
- Multiplica as matrizes em modo serial.
- Multiplica as matrizes em modo paralelo.
- Mede o tempo de cada execucao.
- Valida se os dois resultados sao iguais.
- Exibe `checksum`, amostra da matriz resultado, `speedup` e `eficiencia`.

## Relacao com a metodologia de Foster

- Particionamento: as linhas da matriz resultado sao divididas em blocos independentes.
- Comunicacao: cada worker recebe apenas seu bloco de linhas e a matriz B transposta.
- Aglomeracao: os blocos calculados sao reunidos na ordem correta.
- Mapeamento: os blocos sao distribuidos entre processos, ou threads em fallback.
