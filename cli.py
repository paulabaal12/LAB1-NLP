"""
CLI interactiva para el Laboratorio 1 (Tokenizacion y Guardrails para LLMs).

Permite escribir un texto y ver, en un solo lugar:
- Normalizacion
- Comparacion de tokenizadores (espacios, regex basico, regex mixto)
- Estadisticas del texto
- Datos sensibles detectados (regex)
- Accion de guardrail recomendada y texto seguro resultante

Ejecutar:
    python cli.py
"""

from laboratorio_1_Jose_marchena_Paula_Barillas import (
    normalizar_espacios,
    tokenizar_por_espacios,
    tokenizar_con_regex_basico,
    tokenizar_con_regex_mixto,
    calcular_estadisticas,
    imprimir_estadisticas,
    detectar_datos_sensibles,
    aplicar_guardrail,
)


def imprimir_tokenizadores(texto):
    print("\nTokenizacion por espacios:")
    print(tokenizar_por_espacios(texto))

    print("\nTokenizacion Regex basica:")
    print(tokenizar_con_regex_basico(texto))

    print("\nTokenizacion Regex mixta:")
    print(tokenizar_con_regex_mixto(texto))


def imprimir_datos_sensibles(hallazgos):
    print("\nDatos sensibles detectados:")
    if hallazgos:
        for h in hallazgos:
            print(f"  - {h['tipo']}: {h['valor']}")
    else:
        print("  No se detectaron datos sensibles.")


def procesar_entrada(texto):
    texto_normalizado = normalizar_espacios(texto)

    print("=" * 80)
    print("Texto original:")
    print(texto)

    print("\nTexto normalizado:")
    print(texto_normalizado)

    imprimir_tokenizadores(texto_normalizado)

    tokens = tokenizar_con_regex_mixto(texto_normalizado)
    estadisticas = calcular_estadisticas(texto_normalizado, tokens)
    print("\nEstadisticas (con tokenizacion regex mixta):")
    imprimir_estadisticas(estadisticas)

    resultado_guardrail = aplicar_guardrail(texto_normalizado)
    imprimir_datos_sensibles(resultado_guardrail["hallazgos"])

    print(f"\nAccion recomendada: {resultado_guardrail['accion']}")

    print("\nTexto seguro:")
    if resultado_guardrail["texto_seguro"] is None:
        print("  [BLOQUEADO: no debe enviarse al modelo]")
    else:
        print(resultado_guardrail["texto_seguro"])

    print("=" * 80)
    print()


def main():
    print("CLI - Tokenizacion y Guardrails para LLMs")
    print("Escribe un texto y presiona Enter para analizarlo.")
    print("Escribe 'salir' o 'exit' para terminar.\n")

    while True:
        try:
            texto = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not texto:
            continue
        if texto.lower() in {"salir", "exit", "quit"}:
            break

        procesar_entrada(texto)


if __name__ == "__main__":
    main()
