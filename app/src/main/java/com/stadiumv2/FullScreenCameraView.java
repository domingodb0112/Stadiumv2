package com.stadiumv2;

import android.content.Context;
import android.util.AttributeSet;

import org.opencv.android.CameraBridgeViewBase;
import org.opencv.android.JavaCamera2View;

public class FullScreenCameraView extends JavaCamera2View {

    public FullScreenCameraView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    /**
     * La vista ocupa exactamente el espacio que le da el padre (pantalla completa).
     */
    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        setMeasuredDimension(
                MeasureSpec.getSize(widthMeasureSpec),
                MeasureSpec.getSize(heightMeasureSpec));
    }

    /**
     * Forzamos cover-scale en mScale antes de delegar al padre.
     * Así la imagen llena la vista sin barras negras:
     * mScale = max(viewW/frameW, viewH/frameH)
     * El canvas clipa automáticamente lo que desborda.
     */
    @Override
    protected synchronized void deliverAndDrawFrame(CvCameraViewFrame frame) {
        if (mFrameWidth > 0 && mFrameHeight > 0 && getWidth() > 0 && getHeight() > 0) {
            mScale = Math.max(
                    (float) getWidth() / mFrameWidth,
                    (float) getHeight() / mFrameHeight);
        }
        super.deliverAndDrawFrame(frame);
    }
}