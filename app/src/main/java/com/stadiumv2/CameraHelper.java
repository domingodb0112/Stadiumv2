package com.stadiumv2;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.util.Log;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import org.opencv.android.CameraBridgeViewBase;

public class CameraHelper {
    private static final String TAG = "CameraHelper";
    public static final int PERM_REQ = 100;

    public static boolean hasPermission(Context ctx) {
        return ContextCompat.checkSelfPermission(ctx, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED;
    }

    public static void requestPermission(Activity activity) {
        ActivityCompat.requestPermissions(activity,
                new String[]{Manifest.permission.CAMERA}, PERM_REQ);
    }

    public static void setupCameraIndex(CameraManager manager, CameraBridgeViewBase cameraView) {
        try {
            String[] ids = manager.getCameraIdList();
            if (ids.length == 0) {
                cameraView.setCameraIndex(0);
                return;
            }

            int selectedId = 0;
            for (String id : ids) {
                CameraCharacteristics ch = manager.getCameraCharacteristics(id);
                Integer facing = ch.get(CameraCharacteristics.LENS_FACING);
                if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
                    selectedId = Integer.parseInt(id);
                    break;
                }
            }
            cameraView.setCameraIndex(selectedId);
        } catch (Exception e) {
            Log.e(TAG, "Error: " + e.getMessage());
            cameraView.setCameraIndex(0);
        }
    }
}
