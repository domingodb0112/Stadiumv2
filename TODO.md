# StadiumV2 - Proyecto AR Photo Booth

Este documento detalla el flujo de trabajo, la configuración clave y los requisitos del sistema para el proyecto **StadiumV2**.

## 🚀 Flujo de Trabajo (Workflow)

1.  **Inicio & Selección:**
    *   La app inicia en `MainActivity` mostrando un overlay de bienvenida.
    *   El usuario navega a `PlayerSelectionActivity` para elegir los "jugadores" (videos overlay).
2.  **Experiencia AR (MainActivity):**
    *   Se activa la cámara (preferiblemente frontal).
    *   OpenCV captura frames en tiempo real.
    *   El motor nativo (C++) decodifica videos `.mov` con transparencia y los mezcla con el feed de la cámara mediante `NativeModule.processFrame()`.
3.  **Captura & Cuenta Regresiva:**
    *   El usuario presiona el botón de captura.
    *   Se inicia una cuenta regresiva de 5 segundos.
    *   Al finalizar, se captura un frame mezclado y se guarda en disco.
4.  **Confirmación y Envío:**
    *   `PhotoViewActivity` muestra la foto resultante.
    *   Si el usuario confirma, `FinalActivity` sube la imagen al servidor mediante `NetworkClient`.
    *   Se recibe un código QR del servidor para que el usuario descargue su foto.

---

## ⚙️ Configuraciones Clave

### Tamaño y Posición de Videos
Se configura en `MainActivity.java` dentro del método `startVideoOverlay()`:
- **Método:** `setOverlayTransformV2(slot, x, y, ancho, alto)`
- **Ejemplo:** `setOverlayTransformV2(0, 0, 0, fw, fh);` (Ocupa toda la pantalla).

### Ubicación de Videos
Los videos deben estar en formato `.mov` (con canal alfa/transparencia) en:
- `/sdcard/Android/data/com.stadiumv2/files/`
- O integrados en la carpeta `assets/` del proyecto.

---

## 🛠️ Requisitos de Hardware Recomendados

Para un rendimiento fluido (60 FPS) y fotos de alta calidad:

*   **Tarjeta (SBC):** Orange Pi 5 (8GB RAM) o superior (Rockchip RK3588).
*   **Cámara:** Logitech C922 Pro o Logitech BRIO 4K (Plug & Play UVC).
*   **Resolución:** Configurada a 1080p (1920x1080) para equilibrio entre calidad y velocidad de procesamiento.

---

## 📦 Generación de APK

### Debug (Pruebas rápidas)
- **Comando:** `./gradlew assembleDebug`
- **Ruta:** `app/build/outputs/apk/debug/app-debug.apk`

### Release (Producción/Firma)
1.  **Build > Generate Signed Bundle / APK...**
2.  Seleccionar **APK**.
3.  Usar Keystore existente o crear uno nuevo.
4.  Variante: **release**.
5.  Firmas: Marcar **V1** y **V2**.
- **Ruta:** `app/release/app-release.apk`

---

## 📝 Tareas Pendientes / Mejoras
- [ ] Implementar ajuste dinámico de posición de overlays desde un archivo JSON externo.
- [ ] Optimizar el `NetworkClient` para reintentos automáticos en caso de mala conexión en estadios.
- [ ] Agregar soporte para cambio de resolución en caliente (720p vs 1080p) según la temperatura del procesador.
- [ ] Mejorar la interfaz de selección de jugadores con animaciones más fluidas.
