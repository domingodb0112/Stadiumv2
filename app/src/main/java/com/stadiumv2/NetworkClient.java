package com.stadiumv2;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Base64;
import android.util.Log;
import okhttp3.*;
import org.json.JSONObject;
import java.io.File;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class NetworkClient {
    private static final String TAG = "NetworkClient";
    private static final String UPLOAD_URL = "http://img.mirasintind.org/subir-foto";
    private final OkHttpClient client;

    public interface UploadCallback {
        void onSuccess(Bitmap qr);
        void onError(String msg);
    }

    public NetworkClient() {
        this.client = new OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    public void uploadPhoto(String path, UploadCallback cb) {
        File file = new File(path);
        if (!file.exists()) { cb.onError("Archivo no existe"); return; }

        RequestBody body = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", file.getName(), RequestBody.create(file, MediaType.parse("image/jpeg")))
                .build();

        client.newCall(new Request.Builder().url(UPLOAD_URL).post(body).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) { cb.onError(e.getMessage()); }
            @Override public void onResponse(Call call, Response resp) throws IOException {
                if (!resp.isSuccessful() || resp.body() == null) { cb.onError("Error: " + resp.code()); return; }
                handleResponse(resp.body().string(), cb);
            }
        });
    }

    private void handleResponse(String json, UploadCallback cb) {
        try {
            JSONObject obj = new JSONObject(json);
            String b64 = obj.optString("qr_base64", obj.optString("qr", ""));
            if (b64.isEmpty()) { cb.onError("No QR in JSON"); return; }
            if (b64.contains(",")) b64 = b64.substring(b64.indexOf(",") + 1);
            
            byte[] bytes = Base64.decode(b64.trim(), Base64.DEFAULT);
            Bitmap bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (bmp != null) cb.onSuccess(bmp); else cb.onError("Decode failed");
        } catch (Exception e) {
            Log.e(TAG, "Error: " + e.getMessage());
            cb.onError("Processing error");
        }
    }
}
