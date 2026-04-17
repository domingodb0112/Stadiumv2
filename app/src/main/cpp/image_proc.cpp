#include "image_proc.hpp"
#include <opencv2/imgproc.hpp>
#include <algorithm>

void blendPixels(cv::Mat& bg, const cv::Mat& fg) {
    for (int y = 0; y < bg.rows; ++y) {
        uchar* bgRow = bg.ptr<uchar>(y);
        const uchar* fgRow = fg.ptr<uchar>(y);
        for (int x = 0; x < bg.cols; ++x) {
            const int i = x * 4;
            const uchar a = fgRow[i+3];
            if (a == 0) continue;
            if (a == 255) { memcpy(bgRow+i, fgRow+i, 3); continue; }
            const int inv = 255 - a;
            bgRow[i]   = (uchar)((fgRow[i]*a + bgRow[i]*inv)>>8);
            bgRow[i+1] = (uchar)((fgRow[i+1]*a + bgRow[i+1]*inv)>>8);
            bgRow[i+2] = (uchar)((fgRow[i+2]*a + bgRow[i+2]*inv)>>8);
        }
    }
}

void applyOverlay(cv::Mat& bg, VideoPlayer& p) {
    if (!p.ready) return;
    cv::Mat fg; { std::lock_guard<std::mutex> lk(p.mtx); fg = p.currentFrame.clone(); }
    if (fg.empty()) return;
    cv::Mat fgScaled; cv::resize(fg, fgScaled, cv::Size(p.cfg.w, p.cfg.h));
    int x0 = std::max(p.cfg.x, 0), y0 = std::max(p.cfg.y, 0);
    int x1 = std::min(p.cfg.x + p.cfg.w, bg.cols), y1 = std::min(p.cfg.y + p.cfg.h, bg.rows);
    if (x0 >= x1 || y0 >= y1) return;
    cv::Rect bgRoi(x0, y0, x1 - x0, y1 - y0);
    cv::Rect fgRoi(x0 - p.cfg.x, y0 - p.cfg.y, x1 - x0, y1 - y0);
    cv::Mat bgReg = bg(bgRoi), fgReg = fgScaled(fgRoi);
    blendPixels(bgReg, fgReg);
}
