package com.stadiumv2;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.button.MaterialButton;
import java.util.ArrayList;

public class PlayerSelectionActivity extends AppCompatActivity {

    public static final String EXTRA_SELECTED_VIDEOS = "selected_videos";

    private PlayerData[] mPlayers;
    private TextView mTvCount;
    private MaterialButton mBtnContinue;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
        );
        setContentView(R.layout.activity_player_selection);

        mPlayers = PlayerData.getAll();
        mTvCount = findViewById(R.id.tv_selected_count);
        mBtnContinue = findViewById(R.id.btn_continue);

        RecyclerView rv = findViewById(R.id.rv_players);
        rv.setLayoutManager(new GridLayoutManager(this, 3));
        rv.setAdapter(new PlayerAdapter(mPlayers, this::onSelectionChanged, this));

        mBtnContinue.setOnClickListener(v -> launchCamera());
    }

    private void onSelectionChanged(int count) {
        mTvCount.setText(count + (count == 1 ? " seleccionado" : " seleccionados"));
        mBtnContinue.setEnabled(count > 0);
        mBtnContinue.setBackgroundTintList(
            getColorStateList(count > 0 ? android.R.color.holo_green_light
                                        : android.R.color.darker_gray)
        );
    }

    private void launchCamera() {
        ArrayList<String> videos = new ArrayList<>();
        for (PlayerData p : mPlayers) {
            if (p.selected) videos.add(p.videoFile);
        }
        Intent intent = new Intent(this, MainActivity.class);
        intent.putStringArrayListExtra(EXTRA_SELECTED_VIDEOS, videos);
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(intent);
    }
}
