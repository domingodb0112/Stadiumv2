package com.stadiumv2;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.imageview.ShapeableImageView;

public class PlayerAdapter extends RecyclerView.Adapter<PlayerAdapter.VH> {

    public interface OnSelectionChanged { void onChanged(int selectedCount); }

    private final PlayerData[] mPlayers;
    private final OnSelectionChanged mListener;
    private final Context mContext;

    public PlayerAdapter(PlayerData[] players, OnSelectionChanged listener, Context context) {
        mPlayers = players;
        mListener = listener;
        mContext = context;
    }

    @NonNull @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_player_circle, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int pos) {
        PlayerData p = mPlayers[pos];
        h.ivPlayer.setImageResource(p.drawableRes);
        h.tvName.setText(p.name);

        boolean videoAvailable = VideoManager.isVideoAvailable(mContext, p.videoFile);
        applySelectionState(h, p.selected);
        applyVideoAvailability(h, videoAvailable);

        h.itemView.setOnClickListener(v -> {
            if (!videoAvailable) return; // No se puede seleccionar si no hay video
            p.selected = !p.selected;
            applySelectionState(h, p.selected);
            int count = 0;
            for (PlayerData pd : mPlayers) if (pd.selected) count++;
            mListener.onChanged(count);
        });
    }

    private void applyVideoAvailability(VH h, boolean available) {
        if (!available) {
            h.ivPlayer.setAlpha(0.3f);
            h.tvName.setAlpha(0.4f);
            h.tvName.setText(h.tvName.getText() + "\n\u26a0 Sin video");
        } else {
            h.tvName.setAlpha(1f);
        }
    }

    private void applySelectionState(VH h, boolean selected) {
        h.vRing.setVisibility(selected ? View.VISIBLE : View.INVISIBLE);
        h.ivCheck.setVisibility(selected ? View.VISIBLE : View.INVISIBLE);
        h.ivPlayer.setAlpha(selected ? 1f : 0.55f);
    }

    @Override public int getItemCount() { return mPlayers.length; }

    static class VH extends RecyclerView.ViewHolder {
        ShapeableImageView ivPlayer;
        ImageView ivCheck;
        View vRing;
        TextView tvName;

        VH(View v) {
            super(v);
            ivPlayer = (ShapeableImageView) v.findViewById(R.id.iv_player);
            ivCheck  = v.findViewById(R.id.iv_check);
            vRing    = v.findViewById(R.id.v_ring);
            tvName   = v.findViewById(R.id.tv_name);
        }
    }
}
