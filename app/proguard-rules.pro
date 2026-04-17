# Stadium v2 — ProGuard rules
# Las funciones JNI nativas NO deben ofuscarse
-keepclasseswithmembernames class * {
    native <methods>;
}
# Mantener ambas actividades
-keep class com.stadiumv2.MainActivity { *; }
-keep class com.stadiumv2.PhotoViewActivity { *; }
