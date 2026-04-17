#include <jni.h>
#include <string>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>
#include "video_engine.hpp"
#include "image_proc.hpp"

extern "C" JNIEXPORT jstring JNICALL
Java_com_stadiumv2_NativeModule_getLibVersion(JNIEnv* env, jclass) {
    return env->NewStringUTF("Stadium v2 Modular Engine — v2.1");
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_processFrameNative(JNIEnv*, jclass, jlong matAddr, jlong, jboolean blend) {
    cv::Mat& bg = *(cv::Mat*) matAddr;
    cv::flip(bg, bg, 1);
    if (blend) { applyOverlay(bg, g_players[0]); applyOverlay(bg, g_players[1]); }
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_processStaticFrameNative(JNIEnv*, jclass, jlong matAddr) {
    cv::Mat& bg = *(cv::Mat*) matAddr;
    applyOverlay(bg, g_players[0]); applyOverlay(bg, g_players[1]);
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_stadiumv2_NativeModule_initVideoOverlayV2(JNIEnv* env, jclass, jint slot, jstring jpath) {
    if (slot < 0 || slot > 1) return JNI_FALSE;
    VideoPlayer& p = g_players[slot];
    if (p.running) { p.running = false; if(p.thread.joinable()) p.thread.join(); }
    const char* cp = env->GetStringUTFChars(jpath, 0); std::string path(cp); env->ReleaseStringUTFChars(jpath, cp);
    std::vector<FrameEntry> frms; double f; if(!parseFull(path, frms, f)) return JNI_FALSE;
    p.finished = false; p.running = true; p.thread = std::thread(videoLoop, slot, path, std::move(frms), f);
    return JNI_TRUE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_setOverlayTransformV2(JNIEnv*, jclass, jint slot, jint x, jint y, jint w, jint h) {
    if (slot >= 0 && slot <= 1) g_players[slot].cfg = {x, y, w, h};
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_stopVideoOverlayV2(JNIEnv*, jclass, jint slot) {
    if (slot >= 0 && slot <= 1) {
        g_players[slot].running = false; if(g_players[slot].thread.joinable()) g_players[slot].thread.join();
        std::lock_guard<std::mutex> l(g_players[slot].mtx); g_players[slot].currentFrame.release(); g_players[slot].ready = false;
    }
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_stadiumv2_NativeModule_savePhotoNative(JNIEnv* env, jclass, jlong matAddr, jstring jpath) {
    cv::Mat& src = *(cv::Mat*) matAddr; if (src.empty()) return JNI_FALSE;
    cv::Mat snap = src.clone(); const char* cp = env->GetStringUTFChars(jpath, 0); std::string path(cp); env->ReleaseStringUTFChars(jpath, cp);
    std::thread([snap = std::move(snap), path]() mutable {
        cv::Mat out; if (snap.channels()==4) cv::cvtColor(snap, out, cv::COLOR_RGBA2BGR); else out=snap;
        cv::imwrite(path, out, {cv::IMWRITE_JPEG_QUALITY, 95});
    }).detach(); return JNI_TRUE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_resetVideoV2(JNIEnv*, jclass, jint slot) {
    if (slot >= 0 && slot <= 1) g_players[slot].finished = false;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_stadiumv2_NativeModule_isVideoFinishedV2(JNIEnv*, jclass, jint slot) {
    if (slot < 0 || slot > 1) return JNI_TRUE;
    return g_players[slot].finished ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_stadiumv2_NativeModule_setLoopingV2(JNIEnv*, jclass, jint slot, jboolean lp) {
    if (slot >= 0 && slot <= 1) g_players[slot].looping = lp;
}
