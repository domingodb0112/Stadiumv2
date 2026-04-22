# 🚀 Stadiumv2 High-Performance Architecture Guide

Este documento detalla las optimizaciones críticas implementadas para garantizar una interfaz fluida (30+ FPS) y transiciones instantáneas. **Cualquier cambio en la UI debe respetar estas reglas para no degradar el rendimiento.**

## 1. Gestión de Hardware (Cámara)
- **Archivo:** `camera_manager.py` / `main.py`
- **Lógica:** La cámara se inicializa de forma global en el arranque (`main()`). 
- **Regla de Oro:** **NUNCA** llamar a `cap.release()` dentro de los métodos `on_destroy` de las pantallas. La cámara debe permanecer abierta durante toda la sesión.
- **Acceso:** Usar siempre `CameraManager.get_cap()` para obtener la instancia única.

## 2. Motor de Video (Jugadores)
- **Archivo:** `engine/video_overlay.py`
- **RAM Caching:** Los videos `.mov` se pre-cargan en memoria al inicio. No se lee el disco durante el preview.
- **Persistent Threads:** Los hilos de `VideoPlayer` se inician en el "Warm-up" inicial. No se deben detener (`stop()`) al cambiar de pantalla.
- **Reseteo de Sesión:** Para reiniciar los videos, usar `VideoOverlayEngine.start_experience()`, que vuelve el contador de frames a 0 y quita la pausa.
- **Looping:** Configurado en `False` por requerimiento del usuario (se reproducen una vez y se quedan estáticos).

## 3. Optimización del Preview
- **Resolución Interna:** El preview en vivo se escala a **720x1280** independientemente de la resolución de la cámara. Esto permite procesar 4 videos con transparencia sin lag.
- **Z-Order (Capas):** El orden de dibujado es crítico para la profundidad:
    1. Slot 0 (Atrás - Raúl)
    2. Slot 2 (Atrás - Jorge)
    3. Usuario (Segmentado)
    4. Slot 1 (Adelante - Mateo)
    5. Slot 3 (Adelante - Gilberto)

## 4. Procesamiento en Segundo Plano (IA)
- **Archivo:** `screens/simulation.py` (`PreProcessingEngine`)
- **Lógica:** La segmentación (recorte) de la foto del usuario comienza en un hilo de fondo **en el instante en que se presiona el botón "Capturar"**.
- **Caché:** Cuando el usuario llega a la pantalla de procesamiento final, el recorte ya suele estar listo en el caché, eliminando esperas.

## 5. Integración con Servidor (QR)
- **Lógica:** La subida de la foto ocurre de forma paralela durante la simulación.
- **Endpoint:** `POST http://img.mirasintind.org/subir-foto`.
- **Campo:** Espera un archivo en el campo `file`.
