cmake_minimum_required(VERSION 3.18.1)
project("stadiumv2")

# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Esqueleto JNI puro (sin OpenCV)
# ETAPA 2 — Descomentar el bloque OpenCV más abajo
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# ETAPA 2: OpenCV 4.12
# OpenCV_DIR se pasa desde app/build.gradle via -DOpenCV_DIR=...
# ─────────────────────────────────────────────
find_package(OpenCV 4.12 REQUIRED java)

# ─────────────────────────────────────────────
# Librería nativa principal
# ─────────────────────────────────────────────
add_library(
    native-lib
    SHARED
    native-lib.cpp
    video_engine.cpp
    image_proc.cpp
)

target_include_directories(native-lib PRIVATE ${OpenCV_INCLUDE_DIRS})

# ─────────────────────────────────────────────
# Librerías del sistema Android
#   log      → __android_log_print  (Logcat desde C++)
#   android  → APIs nativas del SO
# ─────────────────────────────────────────────
find_library(log-lib     log)
find_library(android-lib android)

target_link_libraries(native-lib
    ${OpenCV_LIBRARIES}
    ${log-lib}
    ${android-lib}
)

# ─────────────────────────────────────────────
# Flags de optimización para hardware limitado
#   -O2         → optimización sólida sin riesgo en debug
#   -ffast-math → relajar normas IEEE754 (seguro para blending)
#   -DNDEBUG    → desactiva asserts
# ─────────────────────────────────────────────
target_compile_options(native-lib PRIVATE
    -O2
    -ffast-math
    -DNDEBUG
)
