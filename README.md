# Sistema de Gerenciamento da Colônia Aurora Siger

**Autor:** Pedro de Oliveira Reis Sales — RM572709  
**Repositório:** https://github.com/PedroSales-dev/Aurora-Siger-Colonia.git  
**Linguagem:** Python 3 (sem bibliotecas externas)

---

## Explicação do Funcionamento

A colônia Aurora Siger opera em Marte sem possibilidade de controle manual em tempo real devido à latência de comunicação com a Terra. O sistema desenvolvido simula a leitura de sensores e executa, em sequência, quatro módulos autônomos:

1. **Inicialização** — os dados de sensores (bateria, geração, consumo, clima) são organizados em uma estrutura de dicionários hierárquicos.
2. **Previsão** — uma regressão linear calculada manualmente estima a energia eólica esperada a partir da velocidade do vento.
3. **Análise** — o balanço entre geração e consumo é avaliado e um alerta ou sugestão é emitido.
4. **Decisão** — regras lógicas determinam o modo de operação da colônia e quais sistemas podem ser desligados.

O fluxo completo é: **Sensores → Dados → Previsão → Análise → Decisão → Relatório**.

---

## Exemplo de Execução

**Entrada (valores simulados dos sensores):**

| Variável            | Valor  |
|---------------------|--------|
| Bateria             | 65%    |
| Geração solar       | 40 u   |
| Geração eólica      | 15 u   |
| Consumo total       | 70 u   |
| Reserva             | 10 u   |
| Velocidade do vento | 11 m/s |
| Temperatura interna | 22°C   |
| Temperatura externa | -60°C  |

**Saída gerada no terminal:**

```
══════════════════════════════════════════════════════════
  🚀  COLÔNIA AURORA SIGER — RELATÓRIO DO CICLO
══════════════════════════════════════════════════════════

  [ PAINEL DE SENSORES ]
  Bateria   : [█████████████░░░░░░░] 65%
  Geração   : [███████████░░░░░░░░░] 55 u  (solar 40 u + eólico 15 u)
  Consumo   : [██████████████░░░░░░] 70 u
  Reserva   : 10 u
  Vento     : 11 m/s
  Leituras  : [40, 38, 41, 39, 42]  (últimas 5 medições de geração solar)

  [ PREVISÃO DE ENERGIA EÓLICA — REGRESSÃO LINEAR ]
  Modelo ajustado : energia = 2.5 × vento + (0.0)
  Estimativa      : ≈ 27.5 u

  [ ANÁLISE DE ENERGIA ]
  Saldo : -15 u
  Status: ALERTA CRÍTICO: consumo supera geração + reserva!

  [ LÓGICA DE DECISÃO ]
  Modo   : MODO ECONOMIA
  Ação   : Monitorar consumo. Reduzir não essenciais se déficit persistir.

  Eficiência energética do ciclo : 78.6%
```

---

## Organização dos Dados

Os dados da colônia são armazenados em um único **dicionário principal** com quatro seções internas:

- **`energia`** — agrupa bateria, geração solar, geração eólica, consumo e reserva em pares chave-valor de acesso direto e O(1).
- **`clima`** — reúne velocidade do vento e temperaturas interna e externa.
- **`sistemas`** — organiza os sistemas da colônia de forma **hierárquica**: a chave de primeiro nível é a categoria (`suporte_vida`, `nao_essenciais`) e as chaves internas são cada sistema com seu estado (`ativo`) e consumo.
- **`leituras_geracao`** — lista com as últimas 5 leituras de geração solar do ciclo atual. Representa diretamente a estrutura de lista mencionada no enunciado ("organize os dados em listas"), tornando visível o uso sequencial de medições.
- **`historico`** — contém duas listas paralelas (`vento_ms = [8, 10, 12]` e `energia_eol = [20, 25, 30]`) usadas como dataset para a regressão linear. O índice `i` de cada lista forma o par de uma medição histórica.
- **`log`** — lista de strings que registra, em ordem, as saídas de cada módulo durante o ciclo.

A escolha do dicionário como estrutura central se justifica pelo acesso rápido por chave, pela legibilidade do código e pela facilidade de extensão (basta adicionar novas chaves para novos sensores ou sistemas).

---

## Regras de Decisão

A função `tomar_decisao()` aplica quatro regras em ordem de prioridade decrescente. A primeira regra cujas condições forem satisfeitas determina o modo de operação. O suporte à vida (oxigênio, aquecimento, água) **nunca é desligado**, independentemente do modo.

| Prioridade | Condição                              | Modo             | Ação                                      |
|:----------:|---------------------------------------|------------------|-------------------------------------------|
| 1 (maior)  | `bateria < 20%` **E** `consumo > geração` | EMERGÊNCIA       | Desligar todos os sistemas não essenciais |
| 2          | `bateria < 50%`                       | REDUZIR CONSUMO  | Desligar laboratório (maior consumidor)   |
| 3          | `consumo > geração` (bateria ok)      | MODO ECONOMIA    | Monitorar; reduzir opcionais se persistir |
| 4 (menor)  | Todos os parâmetros dentro do esperado | OPERAÇÃO NORMAL  | Manter tudo; considerar armazenar excedente |

A análise de energia (`analisar_energia()`) opera de forma independente e classifica o balanço em quatro níveis: **CRÍTICO** (consumo > geração + reserva), **ALERTA** (consumo > geração), **EXCEDENTE** (saldo > 20 u) ou **OK**.

---

## Modelo de Previsão

A previsão de geração eólica é feita pela função `prever_energia_eolica()`, que internamente chama `calcular_regressao()`. Esta última implementa o **método dos mínimos quadrados** para ajustar uma reta `y = a·x + b` aos dados históricos, onde `x` é a velocidade do vento (m/s) e `y` é a energia eólica gerada (u).

As fórmulas usadas são:

```
a = (n·Σxy  −  Σx·Σy)  /  (n·Σx²  −  (Σx)²)
b = (Σy  −  a·Σx)  /  n
```

Com os dados históricos `vento = [8, 10, 12]` e `energia = [20, 25, 30]`, o modelo ajusta os coeficientes `a = 2.5` e `b = 0.0`, resultando na equação:

```
energia = 2.5 × vento + 0.0
```

Para `vento = 11 m/s`, a estimativa é `≈ 27.5 u` (resultado esperado pelo enunciado: ≈ 27). Toda a matemática é feita com operações nativas do Python (`sum`, `range`, aritmética básica) — sem nenhuma biblioteca externa.

---

## Impacto do Sistema: de Reativo para Preditivo

Sem o sistema desenvolvido, a colônia operaria de forma **reativa**: só seria possível responder a problemas depois que eles acontecessem — por exemplo, desligar sistemas somente após a bateria já ter atingido nível crítico.

Com o sistema, a colônia passa a operar de forma **preditiva em dois níveis**:

- **Previsão contínua** — a regressão linear estima a geração eólica esperada para a próxima janela de tempo com base no histórico de medições. Isso permite antecipar se haverá déficit antes que ele ocorra.
- **Decisão antecipada** — as regras de decisão atuam sobre o estado atual combinado com a tendência prevista, desligando sistemas com antecedência suficiente para evitar emergências.

Na prática, isso significa que a colônia consegue equilibrar seu balanço energético de forma autônoma, reduzindo desperdício quando há excedente e protegendo os sistemas críticos de suporte à vida antes que a situação se torne irreversível.

---

## Repositório

O código-fonte completo está disponível em:

**https://github.com/PedroSales-dev/Aurora-Siger-Colonia.git**

Para executar:

```bash
git clone https://github.com/PedroSales-dev/Aurora-Siger-Colonia.git
cd Aurora-Siger-Colonia
python3 main.py
```

Nenhuma instalação adicional é necessária. O projeto usa apenas Python 3 padrão.
