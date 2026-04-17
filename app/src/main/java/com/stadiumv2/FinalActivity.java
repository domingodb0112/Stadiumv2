package com.stadiumv2;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import org.opencv.android.Utils;
import org.opencv.core.Mat;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import java.util.ArrayList;

public class FinalActivity extends AppCompatActivity {
    public static final String EXTRA_PHOTO_PATH = "final_photo_path";

    private ImageView mIvPhoto, mIvQr;
    private View mContainerQr;
    private TextView mTvTitle, mTvSub, mTvCheckmark;

    // Video animation
    private ArrayList<String> mVideos;
    private Mat mBasePhotoMat;
    private Mat mWorkMat;
    private Bitmap mRenderBitmap;
    private volatile boolean mRendering = false;
    private HandlerThread mRenderThread;
    private Handler mRenderHandler;
    private static final long FRAME_MS = 33; // ~30 fps

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyFullscreenFlags();
        setContentView(R.layout.activity_final);

        mIvPhoto    = findViewById(R.id.iv_final_photo);
        mIvQr       = findViewById(R.id.iv_qr_code);
        mContainerQr = findViewById(R.id.container_qr);
        mTvCheckmark = findViewById(R.id.tv_checkmark);
        mTvTitle    = findViewById(R.id.tv_success_title);
        mTvSub      = findViewById(R.id.tv_success_sub);

        findViewById(R.id.btn_back_to_home).setOnClickListener(v -> returnToCamera());

        String path = getIntent().getStringExtra(EXTRA_PHOTO_PATH);
        mVideos = getIntent().getStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS);

        if (path != null) {
            // Mostrar foto estática mientras carga la animación
            loadPhoto(path);

            // Iniciar animación de jugadores sobre la foto
            startVideoAnimation(path);

            // Subir foto al servidor y obtener QR
            new NetworkClient().uploadPhoto(path, new NetworkClient.UploadCallback() {
                @Override public void onSuccess(Bitmap qr) { runOnUiThread(() -> showQR(qr)); }
                @Override public void onError(String msg)  { runOnUiThread(() -> mTvSub.setText("Error: " + msg)); }
            });
        }

        mIvPhoto.postDelayed(
            () -> UIAnimations.runEntranceAnimation(mTvCheckmark, mTvTitle, mTvSub), 200);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Video animation
    // ─────────────────────────────────────────────────────────────────────────

    private void startVideoAnimation(String photoPath) {
        if (mVideos == null || mVideos.isEmpty()) return;

        // Dimensiones de pantalla (hilo principal)
        DisplayMetrics dm = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getMetrics(dm);
        final int fw = dm.widthPixels;
        final int fh = dm.heightPixels;

        // Arrancar los overlays nativos de video (en su propio hilo C++)
        // SIN looping: se reproduce una sola vez y congela en el último frame
        VideoManager.startExperience(this, fw, fh, mVideos);

        // Hilo dedicado de render
        mRenderThread = new HandlerThread("VideoRender");
        mRenderThread.start();
        mRenderHandler = new Handler(mRenderThread.getLooper());
        mRendering = true;

        mRenderHandler.post(() -> {
            // Cargar foto base como Mat (una sola vez)
            mBasePhotoMat = Imgcodecs.imread(photoPath);
            if (mBasePhotoMat == null || mBasePhotoMat.empty()) return;

            // Convertir BGR → RGBA (igual que el pipeline de cámara)
            Imgproc.cvtColor(mBasePhotoMat, mBasePhotoMat, Imgproc.COLOR_BGR2RGBA);

            // Pre-alocar Mat de trabajo y Bitmap (se reusan cada frame)
            mWorkMat      = new Mat(mBasePhotoMat.size(), mBasePhotoMat.type());
            mRenderBitmap = Bitmap.createBitmap(
                mBasePhotoMat.cols(), mBasePhotoMat.rows(), Bitmap.Config.ARGB_8888);

            // Pequeña pausa para que el motor C++ cargue el primer frame
            try { Thread.sleep(300); } catch (InterruptedException ignored) {}

            scheduleNextFrame();
        });
    }

    private void scheduleNextFrame() {
        if (!mRendering || mRenderHandler == null) return;
        // Una vez que ambos videos terminaron, bajar a 2fps para no gastar CPU
        boolean bothDone = NativeModule.isVideoFinishedV2(0) && NativeModule.isVideoFinishedV2(1);
        long delay = bothDone ? 500L : FRAME_MS;
        mRenderHandler.postDelayed(this::renderFrame, delay);
    }

    private void renderFrame() {
        if (!mRendering || mBasePhotoMat == null || mBasePhotoMat.empty()) return;

        // Resetear al frame base (sin nueva alocación)
        mBasePhotoMat.copyTo(mWorkMat);

        // Mezclar el frame actual del video sobre la foto
        // Si el video terminó, currentFrame tiene el último frame congelado → pose final
        NativeModule.processStaticFrame(mWorkMat);

        // Escribir resultado en el Bitmap pre-alocado
        Utils.matToBitmap(mWorkMat, mRenderBitmap);

        // Actualizar UI en hilo principal
        runOnUiThread(() -> {
            if (mRendering) mIvPhoto.setImageBitmap(mRenderBitmap);
        });

        scheduleNextFrame();
    }

    private void stopRendering() {
        mRendering = false;
        if (mRenderHandler != null) {
            mRenderHandler.removeCallbacksAndMessages(null);
        }
        if (mRenderThread != null) {
            mRenderThread.quitSafely();
            mRenderThread = null;
        }
        if (mWorkMat != null)      { mWorkMat.release();      mWorkMat = null; }
        if (mBasePhotoMat != null) { mBasePhotoMat.release(); mBasePhotoMat = null; }
        NativeModule.stopVideoOverlayV2(0);
        NativeModule.stopVideoOverlayV2(1);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UI helpers
    // ─────────────────────────────────────────────────────────────────────────

    private void applyFullscreenFlags() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    /** Muestra la foto estática mientras el render loop no ha arrancado aún. */
    private void loadPhoto(String path) {
        BitmapFactory.Options opts = new BitmapFactory.Options();
        opts.inPreferredConfig = Bitmap.Config.RGB_565;
        Bitmap bmp = BitmapFactory.decodeFile(path, opts);
        if (bmp != null) mIvPhoto.setImageBitmap(bmp);
    }

    private void showQR(Bitmap qr) {
        if (qr == null) return;
        mIvQr.setImageBitmap(qr);
        mContainerQr.setVisibility(View.VISIBLE);
        mContainerQr.setAlpha(0f);
        mContainerQr.animate().alpha(1f).setDuration(500).start();
        mTvSub.setText("¡Escanea para descargar!");
    }

    private void returnToCamera() {
        startActivity(new Intent(this, MainActivity.class)
            .setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP));
        finish();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Lifecycle
    // ─────────────────────────────────────────────────────────────────────────

    @Override
    protected void onPause() {
        super.onPause();
        stopRendering();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        stopRendering();
    }
}
