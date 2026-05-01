# Plan de Migración: Arquitectura Nanobot para Work Assistant

Este documento detalla el plan de ejecución paso a paso para adaptar la base actual de `work-assistant` hacia una arquitectura inspirada en **Nanobot**, orientada a crear un agente personal modular, ligero y fácil de extender.

## Fase 1: Desacoplamiento del Core (Bucle y Ejecutor)
**Objetivo:** Separar la lógica de conversación del framework de ejecución (LangGraph/LLM).
- [ ] Crear `src/agent/runner.py`: Encargado de la interacción directa con el LLM (llamadas al modelo, gestión de herramientas, manejo de errores).
- [ ] Crear `src/agent/loop.py`: Gestionar el flujo de la conversación (Graph/State de LangGraph). Orquestará los nodos, delegando la ejecución real al `runner.py`.
- [ ] Refactorizar el código actual de `langgraph_agent.py` y `agent.py` para adaptarlo a estas dos responsabilidades separadas.

## Fase 2: Sistema de Eventos y Callbacks (Hooks)
**Objetivo:** Permitir que el agente informe de sus acciones en tiempo real sin acoplarse a ninguna interfaz (como Telegram).
- [ ] Crear `src/agent/hook.py`: Definir interfaces de callbacks (rutinas como `on_tool_start`, `on_tool_end`, `on_message_chunk`, `on_iteration_end`).
- [ ] Integrar estos hooks dentro de los nodos y el runtime de LangGraph en `loop.py`.

## Fase 3: Gestión Dinámica del Contexto (Context & Skills)
**Objetivo:** Ensamblado inteligente del prompt y carga dinámica de herramientas para ahorrar tokens y mejorar la precisión.
- [ ] Crear `src/agent/skills.py` (Skill Registry): Un gestor que cargue dinámicamente los archivos de la carpeta `src/prompts/tools/` (ej. `google_calendar.md`, `notion.md`).
- [ ] Crear `src/agent/context.py` (Context Builder): Una clase que construya el *System Prompt* en tiempo real, uniendo el `main_agent.md`, el historial reciente y solo las *Skills* necesarias.

## Fase 4: Memoria a Largo Plazo (Memory)
**Objetivo:** Otorgar al agente una forma de recordar preferencias del usuario, tareas e información clave a largo plazo.
- [ ] Crear `src/agent/memory.py`: Implementar la lectura/escritura del estado general y preferencias usando archivos `.md` (e.g., `MEMORY.md`, `USER.md`) o directamente hacia una base de Notion.
- [ ] (Opcional) Diseñar un script/proceso "Dream" en background que resuma periódicamente el historial y consolide la memoria para evitar ventanas de contexto infinitas.

## Fase 5: Refactorización de Canales (Interfaces)
**Objetivo:** Convertir las interfaces de usuario (canales) en "clientes tontos" que solo envían inputs y renderizan eventos.
- [ ] Modificar `src/interfaces/telegram/bot.py`.
- [ ] Extraer cualquier inicialización compleja o inyección de prompts fuera del bot.
- [ ] Suscribir la conexión de Telegram a los eventos del sistema de Hooks (Fase 2) de forma asíncrona para soportar mensajería fluida (e.g. streaming de texto o notificaciones de "El agente está buscando en Notion...").

## Fase 6: Tareas Asíncronas (Subagents) - *Fase Futura*
**Objetivo:** Realizar tareas de larga duración sin bloquear el chat principal.
- [ ] Crear `src/agent/subagent.py`: Entorno para invocar "mini agentes" (workers) que realicen investigaciones densas, procesamiento de archivos pesados o web scraping, notificando al evento principal al finalizar.
