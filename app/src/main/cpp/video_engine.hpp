#pragma once
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <opencv2/core.hpp>

struct OverlayConfig {
    int x = 0, y = 0, w = 720, h = 1280;
};

struct FrameEntry { 
    uint64_t fileOffset; 
    uint32_t byteSize; 
};

struct VideoPlayer {
    std::string path;
    cv::Mat currentFrame;
    std::mutex mtx;
    std::atomic_bool running{false};
    std::atomic_bool ready{false};
    std::atomic_bool finished{false};
    bool looping = false;
    std::thread thread;
    OverlayConfig cfg;
};

extern VideoPlayer g_players[2];

bool parseFull(const std::string& path, std::vector<FrameEntry>& frames, double& fps);
void videoLoop(int slot, std::string path, std::vector<FrameEntry> frames, double fps);
