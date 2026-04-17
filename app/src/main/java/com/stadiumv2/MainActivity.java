package com.stadiumv2;

import android.content.Context;
import android.content.Intent;
import android.hardware.camera2.CameraManager;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import org.opencv.android.CameraActivity;
import org.opencv.android.CameraBridgeViewBase;
import org.opencv.android.OpenCVLoader;
import org.opencv.core.Mat;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MainActivity extends CameraActivity implements CameraBridgeViewBase.CvCameraViewListener2 {
    private FullScreenCameraView mCameraView;
    private FloatingActionButton mBtnCapture;
    private android.widget.ImageButton mBtnBack;
    private TextView mTvCountdown;
    private View mStartOverlay;
    private volatile boolean mCapturePending = false, mCountingDown = false;
    private boolean mVideoOverlayStarted = false;
    private int mCamWidth = 1080, mCamHeight = 1920;
    private List<String> mSelectedVideos = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyFullscreen();
        setContentView(R.layout.activity_main);
        if (!OpenCVLoader.initLocal()) { finish(); return; }

        mCameraView  = findViewById(R.id.camera_view);
        mBtnCapture  = findViewById(R.id.btn_capture);
        mBtnBack     = findViewById(R.id.btn_back_to_selection);
        mTvCountdown = findViewById(R.id.tv_countdown);
        mStartOverlay = findViewById(R.id.v_start_overlay);

        mCameraView.setCvCameraViewListener(this);
        CameraHelper.setupCameraIndex((CameraManager) getSystemService(Context.CAMERA_SERVICE), mCameraView);
        mCameraView.setMaxFrameSize(1080, 1920);

        mBtnCapture.setOnClickListener(v -> startCountdown());
        mBtnBack.setOnClickListener(v -> finish());
        findViewById(R.id.btn_start_experience).setOnClickListener(v ->
            startActivity(new Intent(this, PlayerSelectionActivity.class)));
        CameraHelper.requestPermission(this);
        readSelectedVideos(getIntent());
    }

    @Override protected void onNewIntent(Intent i) { super.onNewIntent(i); readSelectedVideos(i); }

    private void readSelectedVideos(Intent i) {
        ArrayList<String> v = i.getStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS);
        if (v != null && !v.isEmpty()) { 
            mSelectedVideos = v; 
            mStartOverlay.setVisibility(View.GONE);
            mBtnBack.setVisibility(View.VISIBLE);
        }
    }

    private void applyFullscreen() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyFullscreen();
        if (CameraHelper.hasPermission(this)) mCameraView.enableView();
        if (!mVideoOverlayStarted && mStartOverlay != null) {
            boolean empty = mSelectedVideos.isEmpty();
            mStartOverlay.setVisibility(empty ? View.VISIBLE : View.GONE);
            mBtnBack.setVisibility(empty ? View.GONE : View.VISIBLE);
        }
        if (mBtnCapture != null) mBtnCapture.setEnabled(true);
    }

    @Override
    protected void onPause() {
        super.onPause();
        mCameraView.disableView();
        NativeModule.stopVideoOverlayV2(0); NativeModule.stopVideoOverlayV2(1);
        mVideoOverlayStarted = false;
    }

    private void startCountdown() {
        if (mCountingDown) return;
        mCountingDown = true;
        mBtnCapture.setVisibility(View.GONE); mTvCountdown.setVisibility(View.VISIBLE);
        new CountDownTimer(5000, 1000) {
            public void onTick(long ms) { mTvCountdown.setText(String.valueOf((int) Math.ceil(ms / 1000.0))); }
            public void onFinish() {
                mTvCountdown.setVisibility(View.GONE); mBtnCapture.setVisibility(View.VISIBLE);
                mCountingDown = false; mCapturePending = true;
            }
        }.start();
    }

    @Override
    public void onCameraViewStarted(int w, int h) {
        mCamWidth = w; mCamHeight = h;
        // Videos no longer start automatically here.
    }

    @Override public void onCameraViewStopped() {}

    @Override
    public Mat onCameraFrame(CameraBridgeViewBase.CvCameraViewFrame frame) {
        Mat rgba = frame.rgba();
        // Disabling AR blending during live preview (blend = false)
        NativeModule.processFrame(rgba, false);

        if (mCapturePending) {
            mCapturePending = false;
            // Launch the Confirmation screen instead of FinalActivity
            saveAndConfirm(rgba.clone());
        }
        return rgba;
    }

    private void saveAndConfirm(Mat snapshot) {
        String path = new File(getExternalFilesDir(null), "temp_user_" + System.currentTimeMillis() + ".jpg").getAbsolutePath();
        if (NativeModule.savePhoto(snapshot, path)) {
            Intent intent = new Intent(this, PhotoViewActivity.class);
            intent.putExtra(PhotoViewActivity.EXTRA_PHOTO_PATH, path);
            intent.putStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS, new ArrayList<>(mSelectedVideos));
            startActivity(intent);
        }
        snapshot.release();
    }

    @Override protected List<? extends CameraBridgeViewBase> getCameraViewList() {
        return Collections.singletonList(mCameraView);
    }
}
