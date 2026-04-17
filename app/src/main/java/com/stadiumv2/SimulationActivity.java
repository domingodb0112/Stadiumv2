package com.stadiumv2;

import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.Handler;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.ProgressBar;
import androidx.appcompat.app.AppCompatActivity;
import org.opencv.android.Utils;
import org.opencv.core.Mat;
import org.opencv.core.Size;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.segmentation.Segmentation;
import com.google.mlkit.vision.segmentation.Segmenter;
import com.google.mlkit.vision.segmentation.selfie.SelfieSegmenterOptions;
import com.google.android.gms.tasks.Tasks;
import android.graphics.BitmapFactory;
import java.nio.ByteBuffer;
import java.io.File;
import java.util.ArrayList;

public class SimulationActivity extends AppCompatActivity {
    private String mPhotoPath;
    private java.util.ArrayList<String> mVideos;
    private ProgressBar mProgress;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        applyFullscreen();
        setContentView(R.layout.activity_simulation);

        mProgress = findViewById(R.id.pb_simulation);
        mPhotoPath = getIntent().getStringExtra(PhotoViewActivity.EXTRA_PHOTO_PATH);
        mVideos = getIntent().getStringArrayListExtra(PlayerSelectionActivity.EXTRA_SELECTED_VIDEOS);

        if (mPhotoPath != null) {
            // "Simulation": Perform the blending ONCE at the start (resource-efficient)
            new Thread(this::processStaticBlending).start();
            startProcessingTimer();
        } else {
            finish();
        }
    }

    private void processStaticBlending() {
        // 1. Load User Photo
        Mat userMat = Imgcodecs.imread(mPhotoPath);
        if (userMat.empty()) return;

        // 2. Load Stadium Background (cancha.png)
        String canchaPath = "C:\\Users\\hecto\\Documents\\Miras Codes\\Stadiumv2\\photos\\cancha.png";
        Mat stadiumMat = Imgcodecs.imread(canchaPath);
        if (stadiumMat.empty()) {
            // Fallback or handle error - if stadium is missing, use userMat as is
            stadiumMat = userMat.clone();
        }

        // Standardize sizes: Resize everything to 1080x1920 for final output
        Size finalSize = new Size(1080, 1920);
        Imgproc.resize(stadiumMat, stadiumMat, finalSize);
        Imgproc.resize(userMat, userMat, finalSize);
        Imgproc.cvtColor(stadiumMat, stadiumMat, Imgproc.COLOR_BGR2RGBA);
        Imgproc.cvtColor(userMat, userMat, Imgproc.COLOR_BGR2RGBA);

        try {
            // 3. AI Segmentation to remove user background
            Bitmap userBitmap = Bitmap.createBitmap(userMat.cols(), userMat.rows(), Bitmap.Config.ARGB_8888);
            Utils.matToBitmap(userMat, userBitmap);

            InputImage image = InputImage.fromBitmap(userBitmap, 0);
            SelfieSegmenterOptions options = new SelfieSegmenterOptions.Builder()
                    .setDetectorMode(SelfieSegmenterOptions.SINGLE_IMAGE_MODE)
                    .build();
            Segmenter segmenter = Segmentation.getClient(options);

            // Run segmentation (blocking since we are in a worker thread)
            com.google.mlkit.vision.segmentation.SegmentationMask mask = Tasks.await(segmenter.process(image));
            ByteBuffer maskBuffer = mask.getBuffer();
            int maskWidth = mask.getWidth();
            int maskHeight = mask.getHeight();

            // 4. Composition: Stadium (Back) + User (Foreground with Mask)
            // Create a resulting Mat based on the stadium background
            Mat finalMat = stadiumMat.clone();

            for (int y = 0; y < maskHeight; y++) {
                for (int x = 0; x < maskWidth; x++) {
                    float confidence = maskBuffer.getFloat();
                    if (confidence > 0.5f) { // Person detected
                        // Blend or directly copy user pixel - simplified here as direct copy
                        double[] userPixel = userMat.get(y, x);
                        finalMat.put(y, x, userPixel);
                    }
                }
            }

            // 5. Add AR Players on top of the stadium + user composite
            NativeModule.processStaticFrame(finalMat);

            // 6. Save final result
            String finalSuffix = "_stadium_" + System.currentTimeMillis() + ".jpg";
            String finalPath = mPhotoPath.replace(".jpg", finalSuffix);
            if (NativeModule.savePhoto(finalMat, finalPath)) {
                mPhotoPath = finalPath;
            }
            
            finalMat.release();
        } catch (Exception e) {
            e.printStackTrace();
            // Fallback: if AI fails, just do the players over the original photo
            NativeModule.processStaticFrame(userMat);
            String finalPath = mPhotoPath.replace(".jpg", "_fallback.jpg");
            if (NativeModule.savePhoto(userMat, finalPath)) mPhotoPath = finalPath;
        }

        userMat.release();
        stadiumMat.release();
    }

    private void startProcessingTimer() {
        new CountDownTimer(6000, 50) {
            @Override
            public void onTick(long ms) {
                if (mProgress != null) mProgress.setProgress(6000 - (int)ms);
            }

            @Override
            public void onFinish() {
                if (mProgress != null) mProgress.setProgress(6000);
                Intent intent = new Intent(SimulationActivity.this, FinalActivity.class);
                intent.putExtra(FinalActivity.EXTRA_PHOTO_PATH, mPhotoPath);
                startActivity(intent);
                finish();
            }
        }.start();
    }

    private void applyFullscreen() {
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }
}
