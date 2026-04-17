package com.stadiumv2;

import org.opencv.core.Mat;

/**
 * NativeModule — Bridge for all JNI calls.
 */
public class NativeModule {
    static {
        System.loadLibrary("c++_shared");
        System.loadLibrary("opencv_java4");
        System.loadLibrary("native-lib");
    }

    // Bridge methods to simplify calling from Activities
    public static void processFrame(Mat bg, boolean blend) {
        processFrameNative(bg.getNativeObjAddr(), 0L, blend);
    }

    public static void processStaticFrame(Mat bg) {
        processStaticFrameNative(bg.getNativeObjAddr());
    }

    public static boolean savePhoto(Mat mat, String path) {
        return savePhotoNative(mat.getNativeObjAddr(), path);
    }

    // Native declarations
    public static native String  getLibVersion();
    private static native void    processFrameNative(long bgMatAddr, long fgMatAddr, boolean blend);
    private static native void    processStaticFrameNative(long matAddr);
    public static native boolean initVideoOverlayV2(int slot, String path);
    public static native void    stopVideoOverlayV2(int slot);
    public static native void    setOverlayTransformV2(int slot, int x, int y, int w, int h);
    public static native void    resetVideoV2(int slot);
    public static native void    setLoopingV2(int slot, boolean looping);
    public static native boolean isVideoFinishedV2(int slot);
    private static native boolean savePhotoNative(long matAddr, String path);
}
