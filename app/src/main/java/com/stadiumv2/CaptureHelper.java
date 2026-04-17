package com.stadiumv2;

import android.content.Context;
import android.content.Intent;
import android.util.DisplayMetrics;
import org.opencv.core.Mat;
import org.opencv.core.Rect;
import java.io.File;

public class CaptureHelper {

    public static void capture(Context ctx, Mat snapshot) {
        File out = new File(ctx.getExternalFilesDir(null),
            "stadium_photo_" + System.currentTimeMillis() + ".jpg");

        DisplayMetrics dm = ctx.getResources().getDisplayMetrics();
        float sW = dm.widthPixels, sH = dm.heightPixels;
        float fW = snapshot.cols(), fH = snapshot.rows();
        float sR = sH / sW, fR = fH / fW;

        Mat cropped = (sR > fR)
            ? new Mat(snapshot, new Rect((int) ((fW - fH / sR) / 2), 0, (int) (fH / sR), (int) fH))
            : new Mat(snapshot, new Rect(0, (int) ((fH - fW * sR) / 2), (int) fW, (int) (fW * sR)));

        if (NativeModule.savePhoto(cropped, out.getAbsolutePath())) {
            ctx.startActivity(new Intent(ctx, FinalActivity.class)
                .putExtra(FinalActivity.EXTRA_PHOTO_PATH, out.getAbsolutePath()));
        }
        snapshot.release();
        if (cropped != snapshot) cropped.release();
    }
}
