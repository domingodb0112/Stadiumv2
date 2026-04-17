#pragma once
#include <opencv2/core.hpp>
#include "video_engine.hpp"

void blendPixels(cv::Mat& bg, const cv::Mat& fg);
void applyOverlay(cv::Mat& bg, VideoPlayer& p);
