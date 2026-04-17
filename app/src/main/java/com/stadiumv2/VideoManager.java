package com.stadiumv2;

import android.content.Context;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;

public class VideoManager {
    private static final String TAG = "VideoManager";

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
                }
                slot++;
            }
        }).start();
    }

    public static File resolveVideoFile(Context ctx, String name) {
        File ext = ctx.getExternalFilesDir(null);
        if (ext != null) {
            File f = new File(ext, name);
            if (f.exists() && f.length() > 0) return f;
        }

        File intFile = new File(ctx.getFilesDir(), name);
        if (intFile.exists() && intFile.length() > 0) return intFile;

        try (InputStream in = ctx.getAssets().open(name);
             FileOutputStream out = new FileOutputStream(intFile)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return intFile;
        } catch (IOException e) {
            Log.e(TAG, "Video not found: " + name);
            return null;
        }
    }
}
