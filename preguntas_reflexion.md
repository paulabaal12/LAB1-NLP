# LAB1-NLP

## Preguntas
Respuestas (basadas en el archivo de evidencia ./evidencia.txt):

1. Que falsos positivos encontraron?
        No hubo casos donde se marcara como sensible algo que claramente no lo era, pero el patron PHONE es muy amplio, pues cualquier secuencia larga de digitos con espacios o guiones se tomarían como telefono si no existiera la prioridad de DPI sobre PHONE en ORDEN_PRIORIDAD.
        Tambien la tokenizacion "rompe" cosas que no son datos sensibles, como GPT-4.1 -> ['GPT', '-', '4', '.', '1'] (TEXTO 7) o 17:20 -> ['17', ':', '20'] (TEXTO 8); no son falsos positivos del guardrail, pero muestran perdida de estructura por la tokenizacion.

2. Que falsos negativos encontraron?
        En TEXTO 4 ("Mi password temporal es NPL123 y el API_KEY=abc123-simulada") solo se detectan las palabras clave "password" y "API_KEY" (tipo SECRET_WORD); el VALOR real de la contrasena
        (NPL123) y del API key (abc123-simulada) nunca se detecta con un patron propio. 
        Si el usuario hubiera escrito unicamente "NPL123" o "abc123-simulada" sin la palabra "password"/"API_KEY", el guardrail no habria detectado nada (ALLOW). Tampoco hay patrones para otros secretos comunes en una empresa real: nombres de personas, direcciones fisicas, numeros de tarjeta de credito, IPs, IBAN, etc.

3. Que informacion se pierde al redactar datos sensibles?
        Al reemplazar por etiquetas genericas como [PHONE_REDACTED] o [DPI_REDACTED] se pierde la capacidad de distinguir un dato de otro: en TEXTO 2 hay dos telefonos distintos (+502 5653-2234 y
        2222-3344) y ambos quedan como el mismo texto "[PHONE_REDACTED]", por lo que ya no se puede saber cual era el numero personal y cual el de soporte. 
        Lo mismo pasa en TEXTO 5 con los dos formatos de DPI y en TEXTO 6 con email/telefono/DPI de una misma persona: se pierde el vinculo entre los distintos datos y el formato original (espacios vs guiones), que podria ser util para validacion o trazabilidad posterior.

4. Regex seria suficiente para proteger informacion de una empresa real?
        Es suficiente regex para proteger info de una empresa real? No. Los patrones son fijos y dependen de formatos predecibles (telefono y DPI de Guatemala, palabras clave en espanol/ingles para secretos). Es facil de evadir: basta con no usar la palabra "password"/"clave" (como casi ocurre en TEXTO 4 con el valor NPL123), cambiar el formato de un numero, usar sinonimos no incluidos en SECRET_WORD, o escribir el dato con caracteres especiales/unicode. Ademas no entiende contexto ni semantica, por lo que no cubre nombres, direcciones, secretos sin palabra clave, ni datos sensibles especificos del negocio (contratos, codigos internos, etc.).

5. Que otra capa de seguridad agregarian?
        - Modelos de NER / deteccion de PII entrenados (spaCy, Presidio, modelos de clasificacion) para complementar el regex con entendimiento semantico y de contexto.
        - Validacion humana (human-in-the-loop) para casos marcados como WARN o de confianza media antes de enviarlos al modelo.
        - Gestion de secretos real (vault, variables de entorno) en vez de permitir que credenciales viajen en texto plano dentro de prompts.
        - Logging y auditoria de los hallazgos y acciones del guardrail, con alertas cuando se detecta un patron BLOCK repetidamente.
        - Cifrado en transito/reposo y control de acceso (RBAC) sobre los logs y textos que pasan por el pipeline.

----
## Reflexión

Este laboratorio dejo claro que tokenizacion y guardrails son dos problemas relacionados pero distintos, y que ninguno se resuelve completamente con herramientas puramente sintacticas como regex. 

Comparar los tres tokenizadores mostro que entre mas simple es el metodo (espacios, regex basico), mas estructura se pierde (URLs, correos y numeros de telefono) terminan fragmentados en pedazos sin sentido, lo cual afectaria directamente a la predicción de cualquier modelo. 

El regex mixto mejora bastante, pero sigue rompiendo casos como "GPT-4.1" o "17:20", lo que confirma que la tokenizacion ideal depende del dominio y del tipo de entidades que importan.

En el lado de guardrails, el ejercicio evidencio que un sistema basado unicamente en expresiones regulares detecta bien lo que sigue un formato predecible (DPI, telefono, correo, URL), pero falla en exactamente el escenario mas peligroso: secretos que no van acompanados de una palabra clave
reconocible. Tambien quedo evidente que redactar con etiquetas genericas protege el dato, pero sacrifica trazabilidad, ya que dos valores distintos del mismo tipo se vuelven indistinguibles despues de la redaccion.

En general, el regex es un buen primer filtro, rapido y explicable, pero debe verse como una capa entre varias, no como la solucion completa a la proteccion de datos sensibles en un sistema con LLMs.