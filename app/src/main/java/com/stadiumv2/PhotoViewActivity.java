package com.stadiumv2;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;

/**
 * PhotoViewActivity — Pantalla de revisión de foto capturada.
 *
 * Opciones:
 *   Reintentar → finish() → vuelve a MainActivity (cámara)
 *   Enviar     → (Etapa 5: animación final + envío)
 */
public class PhotoViewActivity extends AppCompatActivity {

    private static final String TAG = "PhotoView";
    public  static final String EXTRA_PHOTO_PATH = "photo_path";

    private String mPhotoPath;
    private java.util.ArrayList<String> mVideos;
    private CountDownTimer mAutoSendTimer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Mantener modo kiosko
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

        setContentView(R.layout.activity_photo_view);

        mPhotoPath = getIntent().getStringExtra(EXTRA_PHOTO_PATH);
        mVideos = getIntent().getStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS);
        if (mPhotoPath == null) { finish(); return; }

        loadPhoto();

        // Reintentar → volver a la cámara
        findViewById(R.id.btn_retake).setOnClickListener(v -> {
            if (mAutoSendTimer != null) mAutoSendTimer.cancel();
            finish();
        });

        // Enviar → ir a pantalla de simulación (Etapa 5)
        findViewById(R.id.btn_send).setOnClickListener(v -> onSendPhoto());

        startAutoTimer();
    }

    private void startAutoTimer() {
        mAutoSendTimer = new CountDownTimer(5000, 1000) {
            @Override public void onTick(long millisUntilFinished) {
                String btnText = "ENVIAR (" + (int)Math.ceil(millisUntilFinished/1000.0) + "s)";
                android.widget.Button btn = findViewById(R.id.btn_send);
                if (btn != null) btn.setText(btnText);
            }
            @Override public void onFinish() { onSendPhoto(); }
        }.start();
    }

    // ─────────────────────────────────────────────────────────────────────
    // Carga la foto guardada por el hilo C++
    // ─────────────────────────────────────────────────────────────────────
    private void loadPhoto() {
        File file = new File(mPhotoPath);

        if (!file.exists()) {
            // El hilo C++ puede seguir escribiendo — reintentar en 300ms
            new Handler().postDelayed(this::loadPhoto, 300);
            return;
        }

        BitmapFactory.Options opts = new BitmapFactory.Options();
        opts.inPreferredConfig = Bitmap.Config.RGB_565;

        Bitmap bmp = BitmapFactory.decodeFile(mPhotoPath, opts);
        if (bmp == null) {
            Toast.makeText(this, "Error cargando foto", Toast.LENGTH_SHORT).show();
            return;
        }

        ((ImageView) findViewById(R.id.iv_photo)).setImageBitmap(bmp);
        Log.i(TAG, "Foto cargada: " + bmp.getWidth() + "x" + bmp.getHeight());
    }

    // ─────────────────────────────────────────────────────────────────────
    // Enviar foto → Pantalla final con animación de celebración
    // ─────────────────────────────────────────────────────────────────────
    private void onSendPhoto() {
        if (mAutoSendTimer != null) mAutoSendTimer.cancel();
        Log.i(TAG, "Enviar foto: " + mPhotoPath);
        Intent intent = new Intent(this, SimulationActivity.class);
        intent.putExtra(PhotoViewActivity.EXTRA_PHOTO_PATH, mPhotoPath);
        intent.putStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS, mVideos);
        startActivity(intent);
        finish();
    }
}
