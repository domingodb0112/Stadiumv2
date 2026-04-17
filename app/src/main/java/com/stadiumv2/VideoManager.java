package com.stadiumv2;

import android.content.Context;
import android.os.Environment;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;

public class VideoManager {
    private static final String TAG = "VideoManager";

    /**
     * Directorio del kiosko en la tarjeta SD del dispositivo.
     * Copiar los videos aqui con: adb push <video>.mov /sdcard/stadiumv2/videos/
     */
    private static final String KIOSK_VIDEO_DIR = "/sdcard/stadiumv2/videos/";

    public static void startExperience(Context ctx, int fw, int fh, List<String> videoFiles) {
        new Thread(() -> {
            int slot = 0;
            for (String filename : videoFiles) {
                if (slot >= 2) break; // máximo 2 overlays simultáneos
                File f = resolveVideoFile(ctx, filename);
                if (f != null) {
                    final int s = slot;
                    NativeModule.setOverlayTransformV2(s, 0, 0, fw, fh);
                    NativeModule.initVideoOverlayV2(s, f.getAbsolutePath());
                } else {
                    Log.w(TAG, "Video no encontrado para slot " + slot + ": " + filename);
                }
                slot++;
            }
        }).start();
    }

    /** Retorna true si el archivo de video existe en cualquiera de las rutas de búsqueda. */
    public static boolean isVideoAvailable(Context ctx, String name) {
        return resolveVideoFile(ctx, name) != null;
    }

    /**
     * Busca el archivo de video en el siguiente orden de prioridad:
     * 1. /sdcard/stadiumv2/videos/  (kiosko – copiado via adb push)
     * 2. externalFilesDir del app   (Android/data/com.stadiumv2/files/)
     * 3. filesDir interno           (data/data/com.stadiumv2/files/)
     * 4. assets del APK             (com.stadiumv2/assets/ – extraído automáticamente)
     */
    public static File resolveVideoFile(Context ctx, String name) {
        // 1. Ruta del kiosko en SD
        File kioskFile = new File(KIOSK_VIDEO_DIR, name);
        if (kioskFile.exists() && kioskFile.length() > 0) {
            Log.d(TAG, "Video encontrado en kiosko SD: " + kioskFile.getAbsolutePath());
            return kioskFile;
        }

        // 2. externalFilesDir del app
        File extDir = ctx.getExternalFilesDir(null);
        if (extDir != null) {
            File f = new File(extDir, name);
            if (f.exists() && f.length() > 0) {
                Log.d(TAG, "Video encontrado en externalFilesDir: " + f.getAbsolutePath());
                return f;
            }
        }

        // 3. filesDir interno
        File intFile = new File(ctx.getFilesDir(), name);
        if (intFile.exists() && intFile.length() > 0) {
            Log.d(TAG, "Video encontrado en filesDir: " + intFile.getAbsolutePath());
            return intFile;
        }

        // 4. Assets del APK → extraer al filesDir para poder reproducirlo
        try (InputStream in = ctx.getAssets().open(name);
             FileOutputStream out = new FileOutputStream(intFile)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            Log.d(TAG, "Video extraído desde assets: " + intFile.getAbsolutePath());
            return intFile;
        } catch (IOException e) {
            Log.e(TAG, "Video no encontrado en ninguna ruta: " + name);
            return null;
        }
    }
}
