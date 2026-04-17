package com.stadiumv2;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class FinalActivity extends AppCompatActivity {
    public static final String EXTRA_PHOTO_PATH = "final_photo_path";
    private ImageView mIvPhoto, mIvQr;
    private View mContainerQr;
    private TextView mTvTitle, mTvSub, mTvCheckmark;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyFullscreenFlags();
        setContentView(R.layout.activity_final);

        mIvPhoto = findViewById(R.id.iv_final_photo);
        mIvQr = findViewById(R.id.iv_qr_code);
        mContainerQr = findViewById(R.id.container_qr);
        mTvCheckmark = findViewById(R.id.tv_checkmark);
        mTvTitle = findViewById(R.id.tv_success_title);
        mTvSub = findViewById(R.id.tv_success_sub);

        findViewById(R.id.btn_back_to_home).setOnClickListener(v -> returnToCamera());

        String path = getIntent().getStringExtra(EXTRA_PHOTO_PATH);
        if (path != null) {
            loadPhoto(path);
            new NetworkClient().uploadPhoto(path, new NetworkClient.UploadCallback() {
                @Override public void onSuccess(Bitmap qr) { runOnUiThread(() -> showQR(qr)); }
                @Override public void onError(String msg) { runOnUiThread(() -> mTvSub.setText("Error: " + msg)); }
            });
        }
        mIvPhoto.postDelayed(() -> UIAnimations.runEntranceAnimation(mTvCheckmark, mTvTitle, mTvSub), 200);
    }

    private void applyFullscreenFlags() {
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

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
        startActivity(new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP));
        finish();
    }

    @Override protected void onPause() { super.onPause(); NativeModule.stopVideoOverlayV2(0); NativeModule.stopVideoOverlayV2(1); }
    @Override protected void onDestroy() { super.onDestroy(); NativeModule.stopVideoOverlayV2(0); NativeModule.stopVideoOverlayV2(1); }
}
