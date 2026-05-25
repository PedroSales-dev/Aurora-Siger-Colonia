# =============================================================================
#   SISTEMA DE GERENCIAMENTO DA COLÔNIA AURORA SIGER
#   Missão: Gerenciar energia de forma autônoma em Marte
#   Autor: Pedro de Oliveira Reis Sales — RM572709
# =============================================================================


# -----------------------------------------------------------------------------
# MÓDULO 1 — ESTRUTURA DE DADOS
# Organiza as informações da colônia em dicionários hierárquicos e listas.
# A hierarquia principal é: colônia → subsistemas → componentes.
# -----------------------------------------------------------------------------

def criar_colonia(bateria, solar, eolico, consumo, reserva, vento,
                  temp_interna, temp_externa):
    """
    Inicializa e retorna o dicionário principal da colônia.
    Todos os dados de sensores são agrupados por domínio (energia, clima)
    e os sistemas são organizados por prioridade operacional.
    """
    colonia = {
        # --- Dados de energia (leitura dos sensores de geração e consumo) ---
        "energia": {
            "bateria_pct":    bateria,   # carga atual da bateria (%)
            "solar_u":        solar,     # geração solar em unidades (u)
            "eolico_u":       eolico,    # geração eólica em unidades (u)
            "consumo_total_u": consumo,  # consumo total atual (u)
            "reserva_u":      reserva,   # energia armazenada em reserva (u)
        },

        # --- Dados climáticos ---
        "clima": {
            "vento_ms":       vento,          # velocidade do vento (m/s)
            "temp_interna_c": temp_interna,   # temperatura interna (°C)
            "temp_externa_c": temp_externa,   # temperatura externa (°C)
        },

        # --- Sistemas da colônia organizados por prioridade ---
        # Hierarquia: categoria → sistema → {ativo, consumo_u}
        "sistemas": {
            # Prioridade MÁXIMA — nunca podem ser desligados
            "suporte_vida": {
                "oxigenio":    {"ativo": True, "consumo_u": 20},
                "aquecimento": {"ativo": True, "consumo_u": 15},
                "agua":        {"ativo": True, "consumo_u": 10},
            },
            # Prioridade SECUNDÁRIA — desligados em modo economia/emergência
            "nao_essenciais": {
                "laboratorio":    {"ativo": True, "consumo_u": 15},
                "comunicacao_b":  {"ativo": True, "consumo_u": 10},
            },
        },

        # --- Leituras recentes dos sensores (lista de medições do ciclo atual) ---
        # Cada elemento representa uma leitura sequencial de geração (u)
        "leituras_geracao": [solar, solar - 2, solar + 1, solar - 1, solar + 2],

        # --- Histórico para regressão linear: vento (m/s) × energia eólica (u) ---
        # Cada lista[i] forma o par de uma medição histórica registrada
        "historico": {
            "vento_ms":    [8,  10, 12],   # velocidades registradas
            "energia_eol": [20, 25, 30],   # energias correspondentes
        },

        # Log das decisões tomadas neste ciclo
        "log": [],
    }
    return colonia


# -----------------------------------------------------------------------------
# MÓDULO 2 — REGRESSÃO LINEAR SIMPLES
# Calcula a equação da reta y = a*x + b pelo método dos mínimos quadrados,
# sem uso de nenhuma biblioteca externa.
# -----------------------------------------------------------------------------

def calcular_regressao(xs, ys):
    """
    Recebe duas listas paralelas (xs = variável independente,
    ys = variável dependente) e retorna os coeficientes (a, b)
    da reta de melhor ajuste y = a*x + b.

    Fórmulas dos mínimos quadrados:
        a = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        b = (Σy - a*Σx) / n
    """
    n     = len(xs)
    soma_x  = sum(xs)
    soma_y  = sum(ys)
    soma_xy = sum(xs[i] * ys[i] for i in range(n))
    soma_x2 = sum(x ** 2 for x in xs)

    denominador = n * soma_x2 - soma_x ** 2
    if denominador == 0:
        return 0.0, soma_y / n   # reta horizontal se todos os x forem iguais

    a = (n * soma_xy - soma_x * soma_y) / denominador
    b = (soma_y - a * soma_x) / n
    return round(a, 4), round(b, 4)


def prever_energia_eolica(colonia, vento_novo):
    """
    Usa o histórico de dados da colônia para ajustar uma regressão linear
    entre velocidade do vento e geração eólica, e retorna a estimativa
    para a velocidade 'vento_novo' informada.
    """
    hist = colonia["historico"]
    a, b = calcular_regressao(hist["vento_ms"], hist["energia_eol"])
    previsao = round(a * vento_novo + b, 1)

    colonia["log"].append(
        f"Previsão eólica: vento={vento_novo} m/s → ≈{previsao} u  "
        f"[modelo: energia = {a}·vento + {b}]"
    )
    return previsao, a, b


# -----------------------------------------------------------------------------
# MÓDULO 3 — ANÁLISE DE ENERGIA
# Compara geração total com consumo e retorna o alerta adequado.
# -----------------------------------------------------------------------------

def analisar_energia(colonia):
    """
    Avalia o balanço energético atual (geração vs. consumo) e classifica
    a situação em quatro níveis: crítico, alerta, sugestão ou equilíbrio.
    Retorna uma tupla (status, mensagem, saldo).
    """
    e        = colonia["energia"]
    geracao  = e["solar_u"] + e["eolico_u"]
    consumo  = e["consumo_total_u"]
    reserva  = e["reserva_u"]
    saldo    = geracao - consumo

    # Nível 1 — consumo supera geração + reserva: situação crítica
    if consumo > geracao + reserva:
        status = "CRITICO"
        msg    = "ALERTA CRÍTICO: consumo supera geração + reserva!"
    # Nível 2 — consumo supera geração (mas há reserva): alerta moderado
    elif consumo > geracao:
        status = "ALERTA"
        msg    = "ALERTA: consumo maior que geração"
    # Nível 3 — sobra significativa de energia: sugestão de armazenamento
    elif saldo > 20:
        status = "EXCEDENTE"
        msg    = "SUGESTÃO: armazenar energia excedente"
    # Nível 4 — situação equilibrada
    else:
        status = "OK"
        msg    = "Balanço energético equilibrado."

    colonia["log"].append(f"Análise de energia → {msg}")
    return status, msg, saldo


# -----------------------------------------------------------------------------
# MÓDULO 4 — LÓGICA DE DECISÃO
# Aplica regras em ordem de prioridade e retorna a ação tomada.
# O suporte à vida NUNCA é desligado.
# -----------------------------------------------------------------------------

def tomar_decisao(colonia):
    """
    Avalia o estado da bateria e o balanço de energia para escolher
    um modo de operação entre cinco possíveis, em ordem de prioridade:

        Regra 1 (EMERGÊNCIA)      — bateria < 20% E consumo > geração
        Regra 2 (MODO ECONOMIA)   — bateria < 50% E consumo > geração  ← condição combinada
        Regra 3 (ATENÇÃO)         — bateria < 50% (sem déficit)
        Regra 4 (ALERTA)          — consumo > geração (bateria ok)
        Regra 5 (NORMAL)          — todos os parâmetros dentro do esperado

    Sistemas de suporte à vida são SEMPRE mantidos ativos.
    """
    e          = colonia["energia"]
    bateria    = e["bateria_pct"]
    geracao    = e["solar_u"] + e["eolico_u"]
    consumo    = e["consumo_total_u"]
    deficit    = consumo > geracao   # True quando consumo supera geração
    nao_ess    = colonia["sistemas"]["nao_essenciais"]

    # Regra 1: situação crítica — bateria muito baixa E consumo alto
    if bateria < 20 and deficit:
        modo = "EMERGÊNCIA"
        acao = ("Desligar todos os sistemas não essenciais. "
                "Manter APENAS suporte à vida.")
        for s in nao_ess:
            nao_ess[s]["ativo"] = False

    # Regra 2: bateria moderada E consumo alto — condição combinada explícita
    elif bateria < 50 and deficit:
        modo = "MODO ECONOMIA"
        acao = ("Bateria baixa e consumo acima da geração: "
                "desligar laboratório e reduzir consumo imediatamente.")
        nao_ess["laboratorio"]["ativo"] = False

    # Regra 3: bateria baixa, mas geração cobre o consumo — apenas monitorar
    elif bateria < 50:
        modo = "ATENÇÃO"
        acao = ("Bateria abaixo de 50%, porém geração cobre o consumo. "
                "Monitorar e evitar novos gastos desnecessários.")

    # Regra 4: bateria ok, mas há déficit — sugerir redução
    elif deficit:
        modo = "ALERTA"
        acao = ("Consumo maior que geração. "
                "Reduzir sistemas não essenciais se situação persistir.")

    # Regra 5: tudo dentro do esperado
    else:
        modo = "OPERAÇÃO NORMAL"
        acao = "Manter todos os sistemas. Considerar armazenar excedente."

    colonia["log"].append(f"Decisão → {modo}: {acao}")
    return modo, acao


# -----------------------------------------------------------------------------
# MÓDULO 5 — EXIBIÇÃO NO TERMINAL
# Funções auxiliares para apresentar os resultados de forma organizada.
# -----------------------------------------------------------------------------

def barra_progresso(valor, maximo, largura=20):
    """Retorna uma barra de progresso ASCII proporcional ao valor."""
    valor     = max(0, min(valor, maximo))
    preenchido = int((valor / maximo) * largura)
    return "█" * preenchido + "░" * (largura - preenchido)


def exibir_resultado(colonia, previsao, coef_a, coef_b, status, msg, saldo, modo, acao):
    """Imprime um relatório completo do ciclo de análise no terminal."""
    e        = colonia["energia"]
    c        = colonia["clima"]
    geracao  = e["solar_u"] + e["eolico_u"]
    bat      = e["bateria_pct"]

    sep  = "═" * 58
    sub  = "─" * 58

    print(f"\n{sep}")
    print("  COLÔNIA AURORA SIGER — RELATÓRIO DO CICLO")
    print(sep)

    # --- Painel de sensores ---
    print("\n  [ PAINEL DE SENSORES ]")
    print(sub)
    print(f"  Bateria     : [{barra_progresso(bat, 100)}] {bat}%")
    print(f"  Geração     : [{barra_progresso(geracao, 100)}] {geracao} u"
          f"  (solar {e['solar_u']} u + eólico {e['eolico_u']} u)")
    print(f"  Consumo     : [{barra_progresso(e['consumo_total_u'], 100)}]"
          f" {e['consumo_total_u']} u")
    print(f"  Reserva     : {e['reserva_u']} u")
    print(f"  Vento       : {c['vento_ms']} m/s")
    print(f"  Temperatura : interna {c['temp_interna_c']}°C"
          f"  |  externa {c['temp_externa_c']}°C")
    print(f"  Leituras    : {colonia['leituras_geracao']}  (últimas 5 medições de geração solar)")

    # --- Previsão eólica ---
    print(f"\n  [ PREVISÃO DE ENERGIA EÓLICA — REGRESSÃO LINEAR ]")
    print(sub)
    print(f"  Modelo ajustado : energia = {coef_a} × vento + ({coef_b})")
    print(f"  Entrada         : vento = {c['vento_ms']} m/s")
    print(f"  Estimativa      : [{barra_progresso(previsao, 50)}] ≈ {previsao} u")

    # --- Análise de energia ---
    print(f"\n  [ ANÁLISE DE ENERGIA ]")
    print(sub)
    print(f"  Saldo (geração - consumo) : {saldo:+} u")
    print(f"  Status : {msg}")

    # --- Decisão ---
    print(f"\n  [ LÓGICA DE DECISÃO ]")
    print(sub)
    print(f"  Modo   : {modo}")
    print(f"  Ação   : {acao}")

    # --- Estado dos sistemas ---
    print(f"\n  [ ESTADO DOS SISTEMAS ]")
    print(sub)
    for categoria, sistemas in colonia["sistemas"].items():
        print(f"  [{categoria.upper().replace('_', ' ')}]")
        for nome, dados in sistemas.items():
            icone = "✅" if dados["ativo"] else "❌"
            print(f"    {icone}  {nome:<22}  {dados['consumo_u']} u")

    # --- Log do ciclo ---
    print(f"\n  [ LOG DO CICLO ]")
    print(sub)
    for i, entrada in enumerate(colonia["log"], 1):
        print(f"  {i}. {entrada}")

    # --- Eficiência ---
    eficiencia = round((geracao / e["consumo_total_u"]) * 100, 1) \
        if e["consumo_total_u"] > 0 else 0.0
    print(f"\n  Eficiência energética do ciclo : {eficiencia}%")
    print(f"{sep}\n")


# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL — mock de sensores + pipeline completo
# -----------------------------------------------------------------------------

def main():
    """
    Simula a leitura de sensores (dados fixos representando um ciclo real),
    executa todos os módulos do sistema e exibe o relatório consolidado.
    """

    # --- Dados simulados dos sensores (mock) ---
    BATERIA        = 65    # % de carga da bateria
    SOLAR          = 40    # unidades geradas pelo painel solar
    EOLICO         = 15    # unidades geradas pela turbina eólica
    CONSUMO        = 70    # unidades consumidas no ciclo
    RESERVA        = 10    # unidades em reserva
    VENTO          = 11    # m/s — velocidade do vento atual
    TEMP_INTERNA   = 22    # °C
    TEMP_EXTERNA   = -60   # °C

    # 1. Inicializar estrutura de dados da colônia
    colonia = criar_colonia(
        bateria       = BATERIA,
        solar         = SOLAR,
        eolico        = EOLICO,
        consumo       = CONSUMO,
        reserva       = RESERVA,
        vento         = VENTO,
        temp_interna  = TEMP_INTERNA,
        temp_externa  = TEMP_EXTERNA,
    )

    # 2. Previsão de energia eólica via regressão linear
    previsao, coef_a, coef_b = prever_energia_eolica(colonia, VENTO)

    # 3. Análise do balanço energético
    status, msg, saldo = analisar_energia(colonia)

    # 4. Tomada de decisão baseada em regras
    modo, acao = tomar_decisao(colonia)

    # 5. Exibição do relatório final
    exibir_resultado(colonia, previsao, coef_a, coef_b,
                     status, msg, saldo, modo, acao)


# Ponto de entrada
if __name__ == "__main__":
    main()
