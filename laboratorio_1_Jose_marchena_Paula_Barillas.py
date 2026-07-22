"""
CC3103 - Procesamiento de Lenguaje Natural
Laboratorio 1: Tokenizacion y Guardrails para LLMs

Este archivo sirve como guia practica para complementar la presentacion de
Semana 1 y 2. Incluye ejemplos, funciones base y ejercicios marcados con TODO.

Objetivos:
- Comparar diferentes formas de tokenizar texto.
- Calcular estadisticas basicas de texto.
- Detectar datos sensibles usando expresiones regulares.
- Aplicar acciones simples de guardrail: ALLOW, WARN, REDACT o BLOCK.

Ejecutar:
    python laboratorio_1_tokenizacion_guardrails_guia.py
"""

from collections import Counter
import re


# -----------------------------------------------------------------------------
# 1. Textos De Prueba
# -----------------------------------------------------------------------------

TEXTOS_DE_PRUEBA = [
    "Hola!!!   necesito ayuda con mi cuenta :(\n mi correo es paula.reba@example.com",
    "Mi numero es +502 5653-2234 y el de soporte es 2222-3344",
    "La documentacion del curso esta en https://docs.aprendizajeporprocesamiento.com/nlp y en www.aprendizajeporprocesamiento.com/manual.pdf",
    "Mi password temporal es NPL123 y el API_KEY=abc123-simulada",
    "Mi DPI es 1234 56789 0101, tambien lo tengo como 1234-56789-0101",
    "Escribeme a soporte.tecnico@uvg.com o llamame al +502 5653-5566, mi DPI es 9876543210101",
    "El modelo GPT-4.1 respondio: 'No tengo suficiente contexto.'",
    "anticonstitucionalmente, NLP, #IA, la clase CC3103 inicia a las 17:20.",
]


# -----------------------------------------------------------------------------
# 2. Normalizacion Basica
# -----------------------------------------------------------------------------

def normalizar_espacios(texto):
    """Elimina espacios repetidos y saltos de linea innecesarios."""
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_minusculas(texto):
    """Convierte texto a minusculas.

    Nota: no siempre conviene hacer esto. Por ejemplo, Apple y apple pueden
    significar cosas distintas.
    """
    return texto.lower()


# -----------------------------------------------------------------------------
# 3. Tokenizacion Clasica
# -----------------------------------------------------------------------------

def tokenizar_por_espacios(texto):
    """Tokenizacion simple usando espacios.

    Ventaja: facil de entender.
    Limitacion: conserva signos pegados a las palabras y no maneja bien URLs,
    correos o puntuacion.
    """
    return texto.split()


def tokenizar_con_regex_basico(texto):
    """Tokenizacion usando Regex para capturar palabras y numeros.

    Limitacion: puede destruir estructuras como correos, telefonos y URLs.
    """
    return re.findall(r"\b\w+\b", texto.lower())


def tokenizar_con_regex_mixto(texto):
    """Tokenizacion un poco mas cuidadosa.

    Este patron intenta conservar:
    - Correos electronicos
    - URLs
    - Palabras
    - Numeros
    - Algunos signos importantes
    """
    patron = r"https?://\S+|www\.\S+|[\w\.-]+@[\w\.-]+\.\w+|\b\w+\b|[^\w\s]"
    return re.findall(patron, texto, flags=re.UNICODE)


# -----------------------------------------------------------------------------
# 4. Estadisticas De Texto
# -----------------------------------------------------------------------------

def calcular_estadisticas(texto, tokens):
    """Calcula estadisticas basicas de un texto tokenizado."""
    frecuencias = Counter(tokens)

    return {
        "caracteres": len(texto),
        "tokens": len(tokens),
        "tokens_unicos": len(set(tokens)),
        "top_10": frecuencias.most_common(10),
    }


def imprimir_estadisticas(estadisticas):
    """Imprime estadisticas en formato legible."""
    print(f"Caracteres: {estadisticas['caracteres']}")
    print(f"Tokens: {estadisticas['tokens']}")
    print(f"Tokens unicos: {estadisticas['tokens_unicos']}")
    print("Top 10 tokens:")
    for token, frecuencia in estadisticas["top_10"]:
        print(f"  - {token}: {frecuencia}")


# -----------------------------------------------------------------------------
# 5. Patrones Regex Para Guardrails
# -----------------------------------------------------------------------------

PATRONES_SENSIBLES = {
    "EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    "URL": r"https?://\S+|www\.\S+",
    "DPI": r"\b\d{4}[\s\-]?\d{5}[\s\-]?\d{4}\b",
    "PHONE": r"\+?\d[\d\s\-]{7,}\d",
    "SECRET_WORD": r"(?i)\b(password|contrasena|contraseña|passkey|clave|secret|token|api_key|apikey|api key)\b",
    "LONG_NUMBER": r"\b\d{8,}\b",
}

ORDEN_PRIORIDAD = ["EMAIL", "URL", "DPI", "PHONE", "LONG_NUMBER"]

def detectar_datos_sensibles(texto):
    """Detecta datos sensibles evitando reportar el mismo fragmento varias veces."""
    hallazgos = []
    ocupados = []  # rangos ya reclamados por un patron con mayor prioridad

    def se_traslapa(inicio, fin):
        return any(not (fin <= a or inicio >= b) for a, b in ocupados)

    for tipo in ORDEN_PRIORIDAD + ["SECRET_WORD"]:
        patron = PATRONES_SENSIBLES[tipo]
        for m in re.finditer(patron, texto):
            inicio, fin = m.span()
            if tipo != "SECRET_WORD":
                if se_traslapa(inicio, fin):
                    continue
                ocupados.append((inicio, fin))
            hallazgos.append({
                "tipo": tipo,
                "valor": m.group(0),
                "inicio": inicio,
                "fin": fin,
            })

    hallazgos.sort(key=lambda h: h["inicio"])
    return hallazgos

# -----------------------------------------------------------------------------
# 6. Acciones De Guardrail
# -----------------------------------------------------------------------------
def decidir_accion(hallazgos):
    """
    SECRET_WORD                         -> BLOCK
    EMAIL / PHONE / DPI / LONG_NUMBER   -> REDACT
    solo URL                            -> WARN
    nada                                -> ALLOW
    """
    tipos = {h["tipo"] for h in hallazgos}

    if "SECRET_WORD" in tipos:
        return "BLOCK"
    if tipos.intersection({"EMAIL", "PHONE", "DPI", "LONG_NUMBER"}):
        return "REDACT"
    if "URL" in tipos:
        return "WARN"
    return "ALLOW"

ETIQUETAS = {
    "EMAIL": "[EMAIL_REDACTED]",
    "URL": "[URL_REDACTED]",
    "DPI": "[DPI_REDACTED]",
    "PHONE": "[PHONE_REDACTED]",
    "LONG_NUMBER": "[NUMBER_REDACTED]",
}


def redactar_texto(texto, hallazgos):
    """Reemplaza cada hallazgo por su etiqueta, de derecha a izquierda."""
    texto_seguro = texto
    for h in sorted(hallazgos, key=lambda x: x["inicio"], reverse=True):
        if h["tipo"] not in ETIQUETAS:
            continue
        texto_seguro = (
            texto_seguro[:h["inicio"]] + ETIQUETAS[h["tipo"]] + texto_seguro[h["fin"]:]
        )
    return texto_seguro


def aplicar_guardrail(texto):
    hallazgos = detectar_datos_sensibles(texto)
    accion = decidir_accion(hallazgos)

    if accion == "REDACT":
        texto_seguro = redactar_texto(texto, hallazgos)
    elif accion == "BLOCK":
        texto_seguro = None
    else:  # para el caso de ALLOW o WARN dejan el texto tal cual
        texto_seguro = texto

    return {"accion": accion, "hallazgos": hallazgos, "texto_seguro": texto_seguro}

# -----------------------------------------------------------------------------
# 7. Pipeline Completo
# -----------------------------------------------------------------------------

def procesar_texto(texto):
    """Ejecuta el pipeline completo para un texto."""
    texto_normalizado = normalizar_espacios(texto)
    resultado_guardrail = aplicar_guardrail(texto_normalizado)

    texto_para_tokenizar = resultado_guardrail["texto_seguro"]

    if texto_para_tokenizar is None:
        tokens = []
        estadisticas = None
    else:
        tokens = tokenizar_con_regex_mixto(texto_para_tokenizar)
        estadisticas = calcular_estadisticas(texto_para_tokenizar, tokens)

    return {
        "texto_original": texto,
        "texto_normalizado": texto_normalizado,
        "guardrail": resultado_guardrail,
        "tokens": tokens,
        "estadisticas": estadisticas,
    }


def imprimir_resultado_pipeline(resultado, indice):
    """Imprime el resultado completo del pipeline."""
    print("=" * 80)
    print(f"TEXTO {indice}")
    print("=" * 80)

    print("Texto original:")
    print(resultado["texto_original"])

    print("\nTexto normalizado:")
    print(resultado["texto_normalizado"])

    print("\nDatos sensibles detectados:")
    hallazgos = resultado["guardrail"]["hallazgos"]
    if hallazgos:
        for hallazgo in hallazgos:
            print(f"  - {hallazgo['tipo']}: {hallazgo['valor']}")
    else:
        print("  No se detectaron datos sensibles.")

    print(f"\nAccion recomendada: {resultado['guardrail']['accion']}")

    print("\nTexto seguro:")
    if resultado["guardrail"]["texto_seguro"] is None:
        print("  [BLOQUEADO: no debe enviarse al modelo]")
    else:
        print(resultado["guardrail"]["texto_seguro"])

    print("\nTokens:")
    print(resultado["tokens"])

    print("\nEstadisticas:")
    if resultado["estadisticas"] is None:
        print("  No se calcularon estadisticas porque el texto fue bloqueado.")
    else:
        imprimir_estadisticas(resultado["estadisticas"])

    print()


# -----------------------------------------------------------------------------
# 8. Demos Para Clase
# -----------------------------------------------------------------------------

def demo_comparar_tokenizadores():
    """Compara tres formas de tokenizar el mismo texto."""
    texto = "Mi numero es +502 5555-1234 y mi correo es ana@uvg.edu.gt"

    print("=" * 80)
    print("DEMO: COMPARACION DE TOKENIZADORES")
    print("=" * 80)
    print("Texto:")
    print(texto)

    print("\nTokenizacion por espacios:")
    print(tokenizar_por_espacios(texto))

    print("\nTokenizacion Regex basica:")
    print(tokenizar_con_regex_basico(texto))

    print("\nTokenizacion Regex mixta:")
    print(tokenizar_con_regex_mixto(texto))
    print()


def demo_guardrails():
    """Ejecuta el pipeline completo sobre todos los textos de prueba."""
    print("=" * 80)
    print("DEMO: PIPELINE COMPLETO")
    print("=" * 80)
    print()

    for indice, texto in enumerate(TEXTOS_DE_PRUEBA, start=1):
        resultado = procesar_texto(texto)
        imprimir_resultado_pipeline(resultado, indice)


# -----------------------------------------------------------------------------
# 9. Ejercicios Para Estudiantes
# -----------------------------------------------------------------------------

def ejercicio_1_agregar_textos():
    """TODO para estudiantes.

    Agreguen 3 textos nuevos a TEXTOS_DE_PRUEBA:
    - Uno con un correo simulado.
    - Uno con un telefono simulado.
    - Uno con una instruccion sospechosa, por ejemplo una clave o token.
    """
    pass


def ejercicio_2_mejorar_regex_dpi():
    """TODO para estudiantes.

    Agreguen un patron llamado DPI al diccionario PATRONES_SENSIBLES.

    Pista:
    - En Guatemala, un DPI suele tener 13 digitos.
    - Puede aparecer con espacios o guiones.

    Ejemplos que podrian detectar:
    - 1234567890101
    - 1234 56789 0101
    - 1234-56789-0101
    """
    pass


def ejercicio_3_accion_warn():
    """TODO para estudiantes.

    Modifiquen decidir_accion para usar WARN.

    Politica sugerida:
    - SECRET_WORD -> BLOCK
    - EMAIL o PHONE -> REDACT
    - URL -> WARN
    - Sin hallazgos -> ALLOW
    """
    pass


def ejercicio_4_reflexion():
    """Preguntas para responder en el informe.

    1. Que falsos positivos encontraron?
    2. Que falsos negativos encontraron?
    3. Que informacion se pierde al redactar datos sensibles?
    4. Regex seria suficiente para proteger informacion de una empresa real?
    5. Que otra capa de seguridad agregarian?

    Respuestas (basadas en el archivo de evidencia ./evidencia.txt):

    1. Falsos positivos:
       No hubo casos donde se marcara como sensible algo que claramente no
       lo era, pero el patron PHONE (r"\+?\d[\d\s\-]{7,}\d") es muy amplio:
       cualquier secuencia larga de digitos con espacios o guiones (por
       ejemplo un DPI, un codigo de curso largo o un numero de factura)
       calzaria como telefono si no existiera la prioridad de DPI sobre
       PHONE en ORDEN_PRIORIDAD (ver TEXTO 5 y TEXTO 6, donde el DPI se
       reporta correctamente como DPI y no como PHONE gracias a ese orden).
       Tambien la tokenizacion "rompe" cosas que no son datos sensibles,
       como GPT-4.1 -> ['GPT', '-', '4', '.', '1'] (TEXTO 7) o
       17:20 -> ['17', ':', '20'] (TEXTO 8); no son falsos positivos del
       guardrail, pero muestran perdida de estructura por la tokenizacion.

    2. Falsos negativos:
       En TEXTO 4 ("Mi password temporal es NPL123 y el API_KEY=abc123-
       simulada") solo se detectan las palabras clave "password" y
       "API_KEY" (tipo SECRET_WORD); el VALOR real de la contrasena
       (NPL123) y del API key (abc123-simulada) nunca se detecta con un
       patron propio. Si el usuario hubiera escrito unicamente
       "NPL123" o "abc123-simulada" sin la palabra "password"/"API_KEY",
       el guardrail no habria detectado nada (ALLOW). Tampoco hay patrones
       para otros PII comunes en una empresa real: nombres de personas,
       direcciones fisicas, numeros de tarjeta de credito, IPs, IBAN, etc.

    3. Informacion que se pierde al redactar:
       Al reemplazar por etiquetas genericas como [PHONE_REDACTED] o
       [DPI_REDACTED] se pierde la capacidad de distinguir un dato de otro:
       en TEXTO 2 hay dos telefonos distintos (+502 5653-2234 y
       2222-3344) y ambos quedan como el mismo texto "[PHONE_REDACTED]",
       por lo que ya no se puede saber cual era el numero personal y cual
       el de soporte. Lo mismo pasa en TEXTO 5 con los dos formatos de
       DPI y en TEXTO 6 con email/telefono/DPI de una misma persona: se
       pierde el vinculo entre los distintos datos y el formato original
       (espacios vs guiones), que podria ser util para validacion o
       trazabilidad posterior.

    4. Es suficiente regex para proteger info de una empresa real?
       No. Los patrones son fijos y dependen de formatos predecibles
       (telefono y DPI de Guatemala, palabras clave en espanol/ingles para
       secretos). Es facil de evadir: basta con no usar la palabra
       "password"/"clave" (como casi ocurre en TEXTO 4 con el valor
       NPL123), cambiar el formato de un numero, usar sinonimos no
       incluidos en SECRET_WORD, o escribir el dato con caracteres
       especiales/unicode. Ademas no entiende contexto ni semantica, por
       lo que no cubre nombres, direcciones, secretos sin palabra clave,
       ni datos sensibles especificos del negocio (contratos, codigos
       internos, etc.).

    5. Otras capas de seguridad:
       - Modelos de NER / deteccion de PII entrenados (spaCy, Presidio,
         modelos de clasificacion) para complementar el regex con
         entendimiento semantico y de contexto.
       - Validacion humana (human-in-the-loop) para casos marcados como
         WARN o de confianza media antes de enviarlos al modelo.
       - Gestion de secretos real (vault, variables de entorno) en vez de
         permitir que credenciales viajen en texto plano dentro de
         prompts.
       - Logging y auditoria de los hallazgos y acciones del guardrail,
         con alertas cuando se detecta un patron BLOCK repetidamente.
       - Cifrado en transito/reposo y control de acceso (RBAC) sobre los
         logs y textos que pasan por el pipeline.
    """
    pass


# -----------------------------------------------------------------------------
# 10. Programa Principal
# -----------------------------------------------------------------------------

def main():
    demo_comparar_tokenizadores()
    demo_guardrails()


if __name__ == "__main__":
    main()
