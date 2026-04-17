#include "video_engine.hpp"
#include <fstream>
#include <cstring>
#include <chrono>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

VideoPlayer g_players[2];

static inline uint32_t be32(const uint8_t* p) {
    return (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) | (uint32_t(p[2]) << 8) | uint32_t(p[3]);
}

static bool readAtom(std::ifstream& f, uint32_t& sz, char nm[5], size_t& off) {
    uint8_t h[8]; if (!f.read((char*)h, 8)) return false;
    sz = be32(h); memcpy(nm, h+4, 4); nm[4]='\0'; off = (size_t)f.tellg();
    return sz >= 8;
}

static bool findAtomInBuf(const std::vector<uint8_t>& b, const char* n, size_t& o, uint32_t& s) {
    size_t i = 0; while (i+8 <= b.size()) {
        uint32_t sz = be32(b.data()+i); if (sz<8 || i+sz > b.size()) break;
        if (memcmp(b.data()+i+4, n, 4)==0) { o=i+8; s=sz-8; return true; } i += sz;
    } return false;
}

bool parseFull(const std::string& path, std::vector<FrameEntry>& frames, double& fps) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f.is_open()) return false; size_t fs = f.tellg(); f.seekg(0);
    size_t mvO = 0, mvS = 0; while ((size_t)f.tellg() < fs) {
        uint32_t s; char n[5]; size_t o; if (!readAtom(f, s, n, o)) break;
        if (strcmp(n, "moov")==0) { mvO=o; mvS=s-8; break; } f.seekg(o+s-8);
    } if (!mvS) return false; f.seekg(mvO); std::vector<uint8_t> mv(mvS); f.read((char*)mv.data(), mvS);
    auto nav = [&](const std::vector<uint8_t>& b, const char* n) {
        size_t o; uint32_t s; return findAtomInBuf(b, n, o, s) ? std::vector<uint8_t>(b.begin()+o, b.begin()+o+s) : std::vector<uint8_t>();
    };
    auto mdia = nav(nav(mv, "trak"), "mdia");
    size_t mdO; uint32_t mdS, ts=30; if (findAtomInBuf(mdia, "mdhd", mdO, mdS)) ts=be32(mdia.data()+mdO+12);
    auto stbl = nav(nav(mdia, "minf"), "stbl");
    size_t stO; uint32_t stS, sd=ts/30; if (findAtomInBuf(stbl, "stts", stO, stS) && stS>=12) sd=be32(stbl.data()+stO+12);
    fps = (sd>0)?(double)ts/sd:30.0;
    size_t szO; uint32_t szS; findAtomInBuf(stbl, "stsz", szO, szS);
    uint32_t fSz = be32(stbl.data()+szO+4), sCnt = be32(stbl.data()+szO+8);
    std::vector<uint32_t> sizes(sCnt); for(uint32_t i=0; i<sCnt; ++i) sizes[i]=(fSz!=0)?fSz:be32(stbl.data()+szO+12+i*4);
    size_t coO; uint32_t coS; findAtomInBuf(stbl, "stco", coO, coS); uint32_t cCnt=be32(stbl.data()+coO+4);
    std::vector<uint64_t> chunks(cCnt); for(uint32_t i=0; i<cCnt; ++i) chunks[i]=be32(stbl.data()+coO+8+i*4);
    size_t scO; uint32_t scS; findAtomInBuf(stbl, "stsc", scO, scS); uint32_t eCnt=be32(stbl.data()+scO+4);
    frames.clear(); uint32_t sIdx=0; for(uint32_t ci=0; ci<cCnt && sIdx<sCnt; ++ci) {
        uint32_t spc=1; for(int i=eCnt-1;i>=0;--i) if(ci+1>=be32(stbl.data()+scO+8+i*12)) { spc=be32(stbl.data()+scO+12+i*12); break; }
        uint64_t o=chunks[ci]; for(uint32_t s=0;s<spc && sIdx<sCnt;++s) { frames.push_back({o, sizes[sIdx]}); o+=sizes[sIdx]; ++sIdx; }
    } return !frames.empty();
}

void videoLoop(int slot, std::string path, std::vector<FrameEntry> frames, double fps) {
    VideoPlayer& p = g_players[slot];
    std::ifstream f(path, std::ios::binary);
    const auto frameDuration = std::chrono::microseconds((long long)(1e6 / fps * 1.11));
    std::vector<uint8_t> buf; size_t idx = 0;
    while (p.running) {
        auto t0 = std::chrono::steady_clock::now();
        const FrameEntry& fe = frames[idx]; buf.resize(fe.byteSize);
        f.seekg(fe.fileOffset); f.read((char*)buf.data(), fe.byteSize);
        cv::Mat decoded = cv::imdecode(buf, cv::IMREAD_UNCHANGED);
        if (!decoded.empty()) {
            cv::cvtColor(decoded, decoded, cv::COLOR_RGBA2BGRA);
            std::lock_guard<std::mutex> lock(p.mtx); p.currentFrame = std::move(decoded); p.ready = true;
        }
        if (idx == frames.size() - 1 && !p.looping) {
            p.finished = true;
            while (p.running && p.finished) std::this_thread::sleep_for(std::chrono::milliseconds(100));
            if (!p.running) break; idx = 0; continue;
        }
        idx = (idx + 1) % frames.size();
        auto sleep = frameDuration - (std::chrono::steady_clock::now() - t0);
        if (sleep > std::chrono::microseconds(0)) std::this_thread::sleep_for(sleep);
    }
}
