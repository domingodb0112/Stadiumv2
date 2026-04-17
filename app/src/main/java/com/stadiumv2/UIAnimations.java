package com.stadiumv2;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.view.View;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.OvershootInterpolator;

public class UIAnimations {

    public static void runEntranceAnimation(View check, View title, View sub) {
        check.setScaleX(0f); check.setScaleY(0f);
        ObjectAnimator checkFade = ObjectAnimator.ofFloat(check, "alpha", 0f, 1f);
        ObjectAnimator checkScaleX = ObjectAnimator.ofFloat(check, "scaleX", 0f, 1f);
        ObjectAnimator checkScaleY = ObjectAnimator.ofFloat(check, "scaleY", 0f, 1f);
        AnimatorSet checkSet = new AnimatorSet();
        checkSet.playTogether(checkFade, checkScaleX, checkScaleY);
        checkSet.setDuration(500);
        checkSet.setInterpolator(new OvershootInterpolator(2f));

        title.setTranslationY(60f);
        ObjectAnimator titleFade = ObjectAnimator.ofFloat(title, "alpha", 0f, 1f);
        ObjectAnimator titleSlide = ObjectAnimator.ofFloat(title, "translationY", 60f, 0f);
        AnimatorSet titleSet = new AnimatorSet();
        titleSet.playTogether(titleFade, titleSlide);
        titleSet.setDuration(400);
        titleSet.setInterpolator(new DecelerateInterpolator());

        sub.setTranslationY(40f);
        ObjectAnimator subFade = ObjectAnimator.ofFloat(sub, "alpha", 0f, 1f);
        ObjectAnimator subSlide = ObjectAnimator.ofFloat(sub, "translationY", 40f, 0f);
        AnimatorSet subSet = new AnimatorSet();
        subSet.playTogether(subFade, subSlide);
        subSet.setDuration(350);
        subSet.setInterpolator(new DecelerateInterpolator());

        AnimatorSet full = new AnimatorSet();
        full.play(checkSet);
        full.play(titleSet).after(300);
        full.play(subSet).after(500);
        full.start();
    }
}
