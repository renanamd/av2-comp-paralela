# Relatorio de Resultados - Multiplicacao de Matrizes

Este relatorio apresenta os resultados obtidos na execucao do programa de multiplicacao de matrizes nos modos `serial`, `paralela com threads` e `paralela com processos`, utilizando dois conjuntos de dimensoes.

## Cenarios Testados

### Exemplo 1
- Matriz A: `10 x 8`
- Matriz B: `8 x 15`

### Exemplo 2
- Matriz A: `300 x 400`
- Matriz B: `400 x 500`

Em cada exemplo, foram realizados testes com:
- execucao serial;
- execucao com threads usando `2 workers`;
- execucao com threads usando `4 workers`;
- execucao com processos usando `2 workers`;
- execucao com processos usando `4 workers`.

## Resultados Obtidos

| Exemplo | Modo | Workers | Tempo (s) | Observacao |
|---|---|---:|---:|---|
| A `10x8`, B `8x15` | Serial | 1 | `0.000693` | Melhor resultado no caso pequeno |
| A `10x8`, B `8x15` | Threads | 2 | `0.001592` | Mais lento que serial |
| A `10x8`, B `8x15` | Threads | 4 | `0.003091` | Overhead maior com mais threads |
| A `10x8`, B `8x15` | Processos | 2 | `0.279941` | Overhead muito alto |
| A `10x8`, B `8x15` | Processos | 4 | `0.487261` | Pior resultado nesse tamanho |
| A `300x400`, B `400x500` | Serial | 1 | `10.478945` | Referencia base |
| A `300x400`, B `400x500` | Threads | 2 | `10.273383` | Quase igual ao serial |
| A `300x400`, B `400x500` | Threads | 4 | `10.231925` | Pequeno ganho |
| A `300x400`, B `400x500` | Processos | 2 | `7.294500` | Melhor que serial |
| A `300x400`, B `400x500` | Processos | 4 | `5.542249` | Melhor resultado geral |

## Consistencia dos Resultados

As amostras exibidas pelo programa foram iguais entre os modos de execucao de cada exemplo, o que indica consistencia nos valores calculados.

### Amostra do Exemplo 1
```text
90 140 153
136 135 148
204 186 232
```

### Amostra do Exemplo 2
```text
9599 9907 9941
10006 10387 10454
9930 10627 10113
```

## Analise Geral dos Resultados

No exemplo pequeno, a execucao serial foi a mais rapida. Isso acontece porque o custo de criar e coordenar threads e processos foi maior do que o tempo necessario para calcular a multiplicacao. Em outras palavras, o problema era pequeno demais para justificar a paralelizacao.

No exemplo maior, a situacao mudou. O custo computacional da multiplicacao passou a ser suficientemente grande para que a divisao do trabalho compensasse. Nesse caso, a execucao com processos apresentou os melhores resultados, principalmente com `4 workers`, reduzindo o tempo de `10.478945 s` para `5.542249 s`.

As threads apresentaram desempenho muito proximo ao serial, com melhora pequena. Isso e coerente com o comportamento do Python em tarefas intensivas de CPU, devido ao `GIL`, que limita o paralelismo real entre threads nesse tipo de carga.

## Avaliacao da Execucao Serial

### 1. Qual foi o tempo de execucao do seu algoritmo em modo serial? Como voce mediu esse tempo?

Os tempos obtidos em modo serial foram:
- Exemplo 1: `0.000693 s`
- Exemplo 2: `10.478945 s`

A medicao foi feita com `time.perf_counter()`, que fornece um contador de alta resolucao adequado para benchmark.

### 2. Quais aspectos do algoritmo voce percebe que se beneficiariam de uma abordagem paralela?

O calculo das linhas da matriz resultado pode ser executado de forma independente. Cada bloco de linhas pode ser atribuido a um worker diferente, permitindo dividir o trabalho e reduzir o tempo total em problemas maiores.

### 3. Voce utilizou alguma tecnica de otimizacao no codigo serial para reduzir o tempo de execucao? Se sim, quais?

Sim. A principal otimizacao foi a transposicao previa da matriz `B`, permitindo acessar suas colunas como linhas durante o calculo. Isso simplifica a multiplicacao e melhora o acesso aos dados.

### 4. O seu codigo serial apresenta alguma limitacao de desempenho que poderia ser resolvida por computacao paralela? Explique.

Sim. O algoritmo utiliza varios loops em Python puro para calcular cada elemento da matriz resultado. Em matrizes grandes, esse custo cresce bastante e se torna um gargalo. A computacao paralela ajuda justamente a dividir esse trabalho entre varios workers.

### 5. Como voce validou os resultados da execucao serial? Existe alguma verificacao de consistencia no seu codigo?

Nos testes realizados, a consistencia foi observada pela igualdade das amostras exibidas para todos os modos em cada exemplo. Alem disso, o codigo possui a funcao `validar_resultados`, que compara matrizes inteiras, embora no fluxo atual ela nao esteja sendo chamada automaticamente.

### 6. Voce teve dificuldades ao implementar o codigo serial? Quais desafios voce enfrentou?

O principal desafio foi estruturar corretamente a multiplicacao de matrizes e garantir a compatibilidade entre o numero de colunas da matriz `A` e o numero de linhas da matriz `B`. Fora isso, a implementacao serial foi relativamente direta.

### 7. Quais foram os principais bottlenecks identificados na execucao serial do seu programa?

Os principais bottlenecks foram:
- os loops aninhados em Python;
- o produto escalar repetido para cada elemento da matriz resultado;
- o aumento rapido da quantidade de operacoes em matrizes maiores.

### 8. O que voce aprendeu sobre a relacao entre a eficiencia da execucao serial e o uso de recursos computacionais (tempo de CPU, memoria)?

A execucao serial tem baixo overhead de controle e, por isso, funciona muito bem em problemas pequenos. Porem, em problemas maiores, o tempo de CPU cresce bastante porque todo o processamento fica concentrado em um unico fluxo de execucao.

## Avaliacao da Execucao Paralela

### 9. Qual foi o tempo de execucao do seu algoritmo em modo paralelo? Como voce mediu esse tempo?

Os tempos paralelos obtidos foram:

#### Exemplo 1
- Threads com 2 workers: `0.001592 s`
- Threads com 4 workers: `0.003091 s`
- Processos com 2 workers: `0.279941 s`
- Processos com 4 workers: `0.487261 s`

#### Exemplo 2
- Threads com 2 workers: `10.273383 s`
- Threads com 4 workers: `10.231925 s`
- Processos com 2 workers: `7.294500 s`
- Processos com 4 workers: `5.542249 s`

Assim como no modo serial, a medicao foi feita com `time.perf_counter()`.

### 10. Quais recursos voce utilizou para implementar o paralelismo? (Ex: threads, processos, multiprocessing, etc.)

Foram utilizados:
- `ThreadPoolExecutor`
- `ProcessPoolExecutor`

Ambos pertencem ao modulo `concurrent.futures` da biblioteca padrao do Python.

### 11. Como voce adaptou o codigo serial para uma execucao paralela? Houve alguma reestruturacao significativa?

Sim. A matriz resultado foi dividida em blocos de linhas. Cada bloco passou a ser calculado por um worker. Houve reestruturacao para:
- particionar o trabalho;
- enviar blocos para os executores;
- coletar os resultados parciais;
- reordenar e reagrupar os blocos ao final.

### 12. Voce implementou alguma tecnica de sincronizacao entre os processos ou threads paralelos? Como ela foi aplicada?

Nao houve sincronizacao manual com mecanismos como `Lock` ou `Semaphore`. A coordenacao foi feita pelo proprio executor e pela coleta de resultados com `as_completed()`. Depois disso, os blocos foram ordenados e reunidos na posicao correta.

### 13. Quais beneficios voce observou ao aplicar a computacao paralela em relacao a execucao serial?

O principal beneficio apareceu em matrizes maiores, especialmente com processos. Houve reducao significativa do tempo de execucao no Exemplo 2. Ja em problemas pequenos, nao houve ganho, pois o overhead de paralelizacao superou o beneficio.

### 14. Como a metodologia de Foster influenciou sua abordagem para a implementacao paralela? Voce seguiu os principios dessa metodologia?

Sim. A metodologia de Foster influenciou diretamente a implementacao:
- Particionamento: divisao da matriz resultado em blocos de linhas;
- Comunicacao: envio do bloco correspondente e da matriz `B` transposta para cada worker;
- Aglomeracao: reuniao dos blocos calculados;
- Mapeamento: distribuicao dos blocos entre threads ou processos.

### 15. O que voce aprendeu com a comparacao de desempenho entre a execucao serial e paralela? Como a diferenca de tempo de execucao se reflete no desempenho do sistema paralelo?

A comparacao mostrou que paralelizar nem sempre melhora o desempenho. Em problemas pequenos, o custo adicional de coordenacao faz a execucao paralela ficar mais lenta do que a serial. Em problemas maiores, especialmente com processos, o paralelismo passa a compensar e reduz o tempo total de execucao.

Tambem foi possivel observar que:
- threads nao trouxeram ganho expressivo em uma tarefa de CPU;
- processos foram mais eficientes nesse contexto;
- aumentar o numero de workers pode melhorar o desempenho quando o volume de trabalho e grande o suficiente.

## Conclusao

Os testes mostraram que a melhor estrategia depende do tamanho do problema. Para matrizes pequenas, a execucao serial foi superior por evitar overhead. Para matrizes maiores, a execucao paralela com processos foi a melhor escolha, apresentando o menor tempo de execucao com `4 workers`.

Esse comportamento confirma a importancia de avaliar o custo da paralelizacao antes de aplica-la. O trabalho tambem mostrou, na pratica, a diferenca entre o uso de threads e processos em Python para tarefas intensivas de CPU.
