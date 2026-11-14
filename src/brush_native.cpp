#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <numeric>
#include <thread>
#include <vector>

namespace {

inline float clampf(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

inline float smoothstepf(float a, float b, float x) {
    float t = clampf((x - a) / (b - a + 1e-8f), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

struct Stroke {
    float cx, cy, ca, sa, inv_hx, inv_hy, a, h, r, g, b;
    int16_t x0, y0, x1, y1, sp, mip;
};

struct FrameCache {
    int W = 0, H = 0, tx_cnt = 0, ty_cnt = 0;
    std::vector<float> col;
    std::vector<float> hgt;
    std::vector<float> h_woven;
    std::vector<float> h_blur;
    std::vector<float> tmp1;
    std::vector<float> tmp3;
    std::vector<float> bloom_s, bloom_g1, bloom_g2;
    std::vector<int32_t> order;
    std::vector<Stroke> strokes;
    std::vector<std::vector<int32_t>> bins;

    void ensure(int w, int h, int tile) {
        if (W != w || H != h) {
            W = w;
            H = h;
            size_t npix = size_t(W) * size_t(H);
            col.resize(npix * 3);
            hgt.resize(npix);
            h_woven.resize(npix);
            h_blur.resize(npix);
            tmp1.resize(npix);
            tmp3.resize(npix * 3);
            int bw = std::max(1, W / 4);
            int bh = std::max(1, H / 4);
            bloom_s.resize(size_t(bw) * size_t(bh) * 3);
            bloom_g1.resize(size_t(bw) * size_t(bh) * 3);
            bloom_g2.resize(size_t(bw) * size_t(bh) * 3);
        }
        int tc = (W + tile - 1) / tile;
        int tr = (H + tile - 1) / tile;
        if (tc != tx_cnt || tr != ty_cnt) {
            tx_cnt = tc;
            ty_cnt = tr;
            bins.resize(size_t(tc) * size_t(tr));
        }
    }
};

FrameCache& get_cache() {
    static FrameCache cache;
    return cache;
}

// Fast 2-thread separable Gaussian blur for 1 channel with branchless interior
void gaussian_blur_1ch(const float* __restrict src, float* __restrict dst, float* __restrict tmp, int W, int H, float sigma) {
    if (sigma < 0.25f) {
        std::memcpy(dst, src, size_t(W) * size_t(H) * sizeof(float));
        return;
    }
    const int rad = std::min(12, std::max(1, int(std::ceil(sigma * 2.1f))));
    float kern[25];
    float sum = 0.0f;
    const float inv2s2 = 1.0f / (2.0f * sigma * sigma);
    for (int i = -rad; i <= rad; ++i) {
        float w = std::exp(-float(i * i) * inv2s2);
        kern[i + rad] = w;
        sum += w;
    }
    const int klen = 2 * rad + 1;
    for (int i = 0; i < klen; ++i) kern[i] /= sum;
    const float* kp = kern + rad;

    const int midH = H / 2;
    auto hpass = [&](int y0, int y1) {
        const int x_end = W - rad;
        for (int y = y0; y < y1; ++y) {
            const float* __restrict row = src + size_t(y) * W;
            float* __restrict out = tmp + size_t(y) * W;
            for (int x = 0; x < std::min(rad, W); ++x) {
                float acc = 0.0f;
                for (int k = -rad; k <= rad; ++k) {
                    int xx = std::max(0, std::min(W - 1, x + k));
                    acc += row[xx] * kp[k];
                }
                out[x] = acc;
            }
            for (int x = rad; x < x_end; ++x) {
                float acc = 0.0f;
                for (int k = -rad; k <= rad; ++k) {
                    acc += row[x + k] * kp[k];
                }
                out[x] = acc;
            }
            for (int x = std::max(rad, x_end); x < W; ++x) {
                float acc = 0.0f;
                for (int k = -rad; k <= rad; ++k) {
                    int xx = std::max(0, std::min(W - 1, x + k));
                    acc += row[xx] * kp[k];
                }
                out[x] = acc;
            }
        }
    };
    std::thread th1(hpass, 0, midH);
    hpass(midH, H);
    th1.join();

    auto vpass = [&](int y0, int y1) {
        for (int y = y0; y < y1; ++y) {
            float* __restrict out = dst + size_t(y) * W;
            if (y >= rad && y < H - rad) {
                std::memset(out, 0, size_t(W) * sizeof(float));
                for (int k = -rad; k <= rad; ++k) {
                    const float w = kp[k];
                    const float* __restrict row = tmp + size_t(y + k) * W;
                    for (int x = 0; x < W; ++x) {
                        out[x] += row[x] * w;
                    }
                }
            } else {
                std::memset(out, 0, size_t(W) * sizeof(float));
                for (int k = -rad; k <= rad; ++k) {
                    const float w = kp[k];
                    int yy = std::max(0, std::min(H - 1, y + k));
                    const float* __restrict row = tmp + size_t(yy) * W;
                    for (int x = 0; x < W; ++x) {
                        out[x] += row[x] * w;
                    }
                }
            }
        }
    };
    std::thread th2(vpass, 0, midH);
    vpass(midH, H);
    th2.join();
}

void gaussian_blur_rgb(float* __restrict rgb, float* __restrict tmp, int W, int H, float sigma) {
    if (sigma < 0.25f) return;
    const int rad = std::min(12, std::max(1, int(std::ceil(sigma * 2.1f))));
    float kern[25];
    float sum = 0.0f;
    const float inv2s2 = 1.0f / (2.0f * sigma * sigma);
    for (int i = -rad; i <= rad; ++i) {
        float w = std::exp(-float(i * i) * inv2s2);
        kern[i + rad] = w;
        sum += w;
    }
    const int klen = 2 * rad + 1;
    for (int i = 0; i < klen; ++i) kern[i] /= sum;
    const float* kp = kern + rad;

    const int midH = H / 2;
    const int W3 = W * 3;
    auto hpass = [&](int y0, int y1) {
        const int x_end = W - rad;
        for (int y = y0; y < y1; ++y) {
            const float* __restrict row = rgb + size_t(y) * W3;
            float* __restrict out = tmp + size_t(y) * W3;
            for (int x = 0; x < std::min(rad, W); ++x) {
                float r = 0.0f, g = 0.0f, b = 0.0f;
                for (int k = -rad; k <= rad; ++k) {
                    int xx = std::max(0, std::min(W - 1, x + k)) * 3;
                    float w = kp[k];
                    r += row[xx] * w;
                    g += row[xx + 1] * w;
                    b += row[xx + 2] * w;
                }
                out[x * 3] = r; out[x * 3 + 1] = g; out[x * 3 + 2] = b;
            }
            for (int x = rad; x < x_end; ++x) {
                float r = 0.0f, g = 0.0f, b = 0.0f;
                const float* __restrict rp = row + x * 3;
                for (int k = -rad; k <= rad; ++k) {
                    float w = kp[k];
                    r += rp[k * 3] * w;
                    g += rp[k * 3 + 1] * w;
                    b += rp[k * 3 + 2] * w;
                }
                out[x * 3] = r; out[x * 3 + 1] = g; out[x * 3 + 2] = b;
            }
            for (int x = std::max(rad, x_end); x < W; ++x) {
                float r = 0.0f, g = 0.0f, b = 0.0f;
                for (int k = -rad; k <= rad; ++k) {
                    int xx = std::max(0, std::min(W - 1, x + k)) * 3;
                    float w = kp[k];
                    r += row[xx] * w;
                    g += row[xx + 1] * w;
                    b += row[xx + 2] * w;
                }
                out[x * 3] = r; out[x * 3 + 1] = g; out[x * 3 + 2] = b;
            }
        }
    };
    std::thread th1(hpass, 0, midH);
    hpass(midH, H);
    th1.join();

    auto vpass = [&](int y0, int y1) {
        for (int y = y0; y < y1; ++y) {
            float* __restrict out = rgb + size_t(y) * W3;
            std::memset(out, 0, size_t(W3) * sizeof(float));
            if (y >= rad && y < H - rad) {
                for (int k = -rad; k <= rad; ++k) {
                    const float w = kp[k];
                    const float* __restrict row = tmp + size_t(y + k) * W3;
                    for (int x = 0; x < W3; ++x) {
                        out[x] += row[x] * w;
                    }
                }
            } else {
                for (int k = -rad; k <= rad; ++k) {
                    const float w = kp[k];
                    int yy = std::max(0, std::min(H - 1, y + k));
                    const float* __restrict row = tmp + size_t(yy) * W3;
                    for (int x = 0; x < W3; ++x) {
                        out[x] += row[x] * w;
                    }
                }
            }
        }
    };
    std::thread th2(vpass, 0, midH);
    vpass(midH, H);
    th2.join();
}

// Clip [x0, x1] to linear range lo <= val0 + step * (x - x0) < hi
inline void clip_linear(float val0, float step, float lo, float hi, int x0, int& ix0, int& ix1) {
    if (std::fabs(step) < 1e-12f) {
        if (val0 < lo || val0 >= hi) {
            ix0 = 1;
            ix1 = 0;
        }
        return;
    }
    float t0 = (lo - val0) / step;
    float t1 = (hi - val0) / step;
    if (step < 0.0f) std::swap(t0, t1);
    int a = x0 + int(std::ceil(t0));
    int b = x0 + int(std::ceil(t1)) - 1;  // strictly < hi (unless exact)
    if (a > ix0) ix0 = a;
    if (b < ix1) ix1 = b;
}

}  // namespace

extern "C" {

void render_frame_native(
    int W, int H, int n_spr, int mip_w0, int mip_h0,
    const float* sprA0, const float* sprA1, const float* sprA2, const float* sprA3,
    const float* sprT0, const float* sprT1, const float* sprT2, const float* sprT3,
    int N,
    const float* sx, const float* sy, const float* ang,
    const float* L, const float* Wd, const int32_t* spr,
    const float* rgb, const float* alpha, const float* hb, const float* zo,
    const float* wv, const float* grain, const float* lo_tex, const float* vig,
    float canvas_r, float canvas_g, float canvas_b,
    float tone_amt, float relief_amt, float bloom_amt, float fade_amt,
    uint8_t* out_rgb24
) {
    const int TILE = 96;
    FrameCache& fc = get_cache();
    fc.ensure(W, H, TILE);

    const size_t npix = size_t(W) * size_t(H);
    float* __restrict col = fc.col.data();
    float* __restrict hgt = fc.hgt.data();

    // Initialize canvas + zero height (2 threads)
    {
        size_t mid = npix / 2;
        auto init_fn = [&](size_t i0, size_t i1) {
            for (size_t i = i0; i < i1; ++i) {
                float m = 1.0f + 0.012f * lo_tex[i];
                col[i * 3 + 0] = canvas_r * m;
                col[i * 3 + 1] = canvas_g * m;
                col[i * 3 + 2] = canvas_b * m;
                hgt[i] = 0.0f;
            }
        };
        std::thread ti(init_fn, 0, mid);
        init_fn(mid, npix);
        ti.join();
    }

    if (N > 0) {
        fc.order.resize(N);
        std::iota(fc.order.begin(), fc.order.end(), 0);
        std::stable_sort(fc.order.begin(), fc.order.end(), [&](int32_t a, int32_t b) {
            return zo[a] < zo[b];
        });

        fc.strokes.clear();
        fc.strokes.reserve(N);
        for (auto& b : fc.bins) b.clear();

        const int tx_cnt = fc.tx_cnt;
        const int ty_cnt = fc.ty_cnt;

        for (int idx = 0; idx < N; ++idx) {
            int i = fc.order[idx];
            float a = alpha[i];
            if (a <= 0.002f) continue;
            float len = L[i];
            float wid = Wd[i];
            if (len < 0.8f || wid < 0.8f) continue;

            float hx = 0.5f * len;
            float hy = 0.5f * wid;
            float th = ang[i];
            float ca = std::cos(th);
            float sa = std::sin(th);
            float rx = std::fabs(ca) * hx + std::fabs(sa) * hy + 1.5f;
            float ry = std::fabs(sa) * hx + std::fabs(ca) * hy + 1.5f;
            float cx = sx[i];
            float cy = sy[i];

            int ix0 = std::max(0, int(std::floor(cx - rx)));
            int ix1 = std::min(W - 1, int(std::ceil(cx + rx)));
            int iy0 = std::max(0, int(std::floor(cy - ry)));
            int iy1 = std::min(H - 1, int(std::ceil(cy + ry)));
            if (ix0 > ix1 || iy0 > iy1) continue;

            int mip = 0;
            if (len < 28.0f && wid < 12.0f) mip = 3;
            else if (len < 56.0f && wid < 22.0f) mip = 2;
            else if (len < 110.0f && wid < 42.0f) mip = 1;

            int sp = spr[i];
            if (sp < 0) sp = 0;
            else if (sp >= n_spr) sp = n_spr - 1;

            Stroke st;
            st.cx = cx;
            st.cy = cy;
            st.ca = ca;
            st.sa = sa;
            st.inv_hx = 1.0f / hx;
            st.inv_hy = 1.0f / hy;
            st.a = a;
            st.h = hb[i];
            st.r = rgb[i * 3 + 0];
            st.g = rgb[i * 3 + 1];
            st.b = rgb[i * 3 + 2];
            st.x0 = int16_t(ix0);
            st.y0 = int16_t(iy0);
            st.x1 = int16_t(ix1);
            st.y1 = int16_t(iy1);
            st.sp = int16_t(sp);
            st.mip = int16_t(mip);

            int32_t sid = int32_t(fc.strokes.size());
            fc.strokes.push_back(st);

            int bx0 = ix0 / TILE;
            int bx1 = ix1 / TILE;
            int by0 = iy0 / TILE;
            int by1 = iy1 / TILE;
            for (int by = by0; by <= by1; ++by) {
                size_t row_off = size_t(by) * tx_cnt;
                for (int bx = bx0; bx <= bx1; ++bx) {
                    fc.bins[row_off + bx].push_back(sid);
                }
            }
        }

        const float* mipA[4] = {sprA0, sprA1, sprA2, sprA3};
        const float* mipT[4] = {sprT0, sprT1, sprT2, sprT3};
        const int mipW[4] = {mip_w0, mip_w0 / 2, mip_w0 / 4, mip_w0 / 8};
        const int mipH[4] = {mip_h0, mip_h0 / 2, mip_h0 / 4, mip_h0 / 8};

        const int n_tiles = tx_cnt * ty_cnt;
        const auto& strokes = fc.strokes;
        const auto& bins = fc.bins;

        auto worker = [&](int tid, int nthreads) {
            for (int tile_id = tid; tile_id < n_tiles; tile_id += nthreads) {
                const auto& list = bins[tile_id];
                if (list.empty()) continue;
                int bx = tile_id % tx_cnt;
                int by = tile_id / tx_cnt;
                int tx0 = bx * TILE;
                int ty0 = by * TILE;
                int tx1 = std::min(W - 1, tx0 + TILE - 1);
                int ty1 = std::min(H - 1, ty0 + TILE - 1);

                for (int32_t sid : list) {
                    const Stroke& st = strokes[sid];
                    const int x0 = std::max(tx0, int(st.x0));
                    const int x1 = std::min(tx1, int(st.x1));
                    const int y0 = std::max(ty0, int(st.y0));
                    const int y1 = std::min(ty1, int(st.y1));

                    const int sw = mipW[st.mip];
                    const int sh = mipH[st.mip];
                    const float* __restrict sA = mipA[st.mip] + size_t(st.sp) * sw * sh;
                    const float* __restrict sT = mipT[st.mip] + size_t(st.sp) * sw * sh;
                    const float half_sw = 0.5f * (sw - 1);
                    const float half_sh = 0.5f * (sh - 1);
                    const float lim_u = float(sw - 1) - 1e-4f;
                    const float lim_v = float(sh - 1) - 1e-4f;

                    const float dudx = st.ca * st.inv_hx * half_sw;
                    const float dvdx = -st.sa * st.inv_hy * half_sh;
                    const float dx0 = float(x0) - st.cx;
                    const float u_base_dx = dx0 * st.ca;
                    const float v_base_dx = -dx0 * st.sa;

                    for (int y = y0; y <= y1; ++y) {
                        const float dy = float(y) - st.cy;
                        const float u_x0 = ((u_base_dx + dy * st.sa) * st.inv_hx + 1.0f) * half_sw;
                        const float v_x0 = ((v_base_dx + dy * st.ca) * st.inv_hy + 1.0f) * half_sh;

                        int ix0 = x0, ix1 = x1;
                        clip_linear(u_x0, dudx, 0.0f, lim_u, x0, ix0, ix1);
                        clip_linear(v_x0, dvdx, 0.0f, lim_v, x0, ix0, ix1);
                        if (ix0 > ix1) continue;

                        float u = u_x0 + float(ix0 - x0) * dudx;
                        float v = v_x0 + float(ix0 - x0) * dvdx;

                        float* __restrict crow = col + size_t(y) * W * 3;
                        float* __restrict hrow = hgt + size_t(y) * W;

                        for (int x = ix0; x <= ix1; ++x, u += dudx, v += dvdx) {
                            const int iu = int(u);
                            const int iv = int(v);
                            const float fu = u - float(iu);
                            const float fv = v - float(iv);
                            const float omfu = 1.0f - fu;
                            const float omfv = 1.0f - fv;
                            const size_t idx00 = size_t(iv) * sw + iu;

                            const float a0 = sA[idx00] * omfu + sA[idx00 + 1] * fu;
                            const float a1 = sA[idx00 + sw] * omfu + sA[idx00 + sw + 1] * fu;
                            const float alpha_px = (a0 * omfv + a1 * fv) * st.a;
                            if (alpha_px <= 0.002f) continue;

                            const float t0 = sT[idx00] * omfu + sT[idx00 + 1] * fu;
                            const float t1 = sT[idx00 + sw] * omfu + sT[idx00 + sw + 1] * fu;
                            const float st_val = t0 * omfv + t1 * fv;

                            const float shade = (1.0f + tone_amt * st_val) * alpha_px;
                            const float inv_a = 1.0f - alpha_px;
                            float* __restrict cp = crow + x * 3;
                            cp[0] = cp[0] * inv_a + st.r * shade;
                            cp[1] = cp[1] * inv_a + st.g * shade;
                            cp[2] = cp[2] * inv_a + st.b * shade;
                            hrow[x] = hrow[x] * (1.0f - 0.65f * alpha_px) + st.h * (0.65f + 0.35f * st_val) * alpha_px;
                        }
                    }
                }
            }
        };

        std::thread t0(worker, 0, 2);
        worker(1, 2);
        t0.join();
    }

    // 1. Add flax weave where paint is thin (2 threads), then smooth height for Sobel
    const float rs = float(H) / 1080.0f;
    float* __restrict h_woven = fc.h_woven.data();
    {
        size_t mid = npix / 2;
        auto wv_fn = [&](size_t i0, size_t i1) {
            for (size_t i = i0; i < i1; ++i) {
                float h = hgt[i];
                float thin = 1.2f - clampf(h, 0.0f, 1.0f);
                h_woven[i] = h + 0.10f * wv[i] * thin;
            }
        };
        std::thread tw(wv_fn, 0, mid);
        wv_fn(mid, npix);
        tw.join();
    }
    float* __restrict h_blur = fc.h_blur.data();
    gaussian_blur_1ch(h_woven, h_blur, fc.tmp1.data(), W, H, 0.72f * std::max(rs, 0.6f));

    // 2. Soften colour buffer slightly
    gaussian_blur_rgb(col, fc.tmp3.data(), W, H, 0.58f * std::max(rs, 0.5f));

    // 3. Directional impasto Sobel relief + fine grain (2 threads)
    {
        int midH = H / 2;
        auto shade_pass = [&](int y0, int y1) {
            for (int y = y0; y < y1; ++y) {
                const int ym = std::max(0, y - 1);
                const int yp = std::min(H - 1, y + 1);
                const float* __restrict rm = h_blur + size_t(ym) * W;
                const float* __restrict r0 = h_blur + size_t(y) * W;
                const float* __restrict rp = h_blur + size_t(yp) * W;
                float* __restrict c_row = col + size_t(y) * W * 3;
                const float* __restrict g_row = grain + size_t(y) * W;
                for (int x = 0; x < W; ++x) {
                    const int xm = std::max(0, x - 1);
                    const int xp = std::min(W - 1, x + 1);
                    float gx = (rm[xp] + 2.0f * r0[xp] + rp[xp]) - (rm[xm] + 2.0f * r0[xm] + rp[xm]);
                    float gy = (rp[xm] + 2.0f * rp[x] + rp[xp]) - (rm[xm] + 2.0f * rm[x] + rm[xp]);
                    float sh = clampf(1.0f - relief_amt * 0.13f * (gx * 0.7f + gy * 0.7f), 0.80f, 1.22f);
                    float gmul = sh * (1.0f + 0.012f * g_row[x]);
                    c_row[x * 3 + 0] *= gmul;
                    c_row[x * 3 + 1] *= gmul;
                    c_row[x * 3 + 2] *= gmul;
                }
            }
        };
        std::thread th(shade_pass, 0, midH);
        shade_pass(midH, H);
        th.join();
    }

    // 4. Quarter-resolution multi-scale optical highlight bloom (2 threads)
    if (bloom_amt > 0.001f) {
        const int bW = std::max(1, W / 4);
        const int bH = std::max(1, H / 4);
        float* __restrict small = fc.bloom_s.data();
        const int midbH = bH / 2;
        auto down_fn = [&](int by0, int by1) {
            for (int by = by0; by < by1; ++by) {
                const int ystart = by * 4;
                for (int bx = 0; bx < bW; ++bx) {
                    const int xstart = bx * 4;
                    float sr = 0.0f, sg = 0.0f, sb = 0.0f;
                    int cnt = 0;
                    for (int dy = 0; dy < 4 && ystart + dy < H; ++dy) {
                        const float* __restrict crow = col + size_t(ystart + dy) * W * 3;
                        for (int dx = 0; dx < 4 && xstart + dx < W; ++dx) {
                            const float* cp = crow + (xstart + dx) * 3;
                            float r = cp[0], g = cp[1], b = cp[2];
                            float lum = std::max(r, std::max(g, b));
                            float w = smoothstepf(0.72f, 1.02f, lum);
                            sr += r * w; sg += g * w; sb += b * w;
                            ++cnt;
                        }
                    }
                    float inv = 1.0f / std::max(1, cnt);
                    float* __restrict out = small + (size_t(by) * bW + bx) * 3;
                    out[0] = sr * inv; out[1] = sg * inv; out[2] = sb * inv;
                }
            }
        };
        std::thread td(down_fn, 0, midbH);
        down_fn(midbH, bH);
        td.join();

        const size_t b_floats = size_t(bW) * size_t(bH) * 3;
        std::memcpy(fc.bloom_g1.data(), small, b_floats * sizeof(float));
        std::memcpy(fc.bloom_g2.data(), small, b_floats * sizeof(float));
        gaussian_blur_rgb(fc.bloom_g1.data(), fc.tmp3.data(), bW, bH, std::max(0.8f, 3.5f * rs));
        gaussian_blur_rgb(fc.bloom_g2.data(), fc.tmp3.data(), bW, bH, std::max(1.5f, 11.0f * rs));

        const float* __restrict g1 = fc.bloom_g1.data();
        const float* __restrict g2 = fc.bloom_g2.data();
        const int midH = H / 2;
        auto up_fn = [&](int y0_p, int y1_p) {
            for (int y = y0_p; y < y1_p; ++y) {
                float fy = (float(y) + 0.5f) * 0.25f - 0.5f;
                int y0 = int(clampf(std::floor(fy), 0.0f, float(bH - 1)));
                int y1 = std::min(bH - 1, y0 + 1);
                float wy = clampf(fy - y0, 0.0f, 1.0f);
                const float* __restrict r_y0 = g1 + size_t(y0) * bW * 3;
                const float* __restrict r_y1 = g1 + size_t(y1) * bW * 3;
                const float* __restrict r2_y0 = g2 + size_t(y0) * bW * 3;
                const float* __restrict r2_y1 = g2 + size_t(y1) * bW * 3;
                float* __restrict c_row = col + size_t(y) * W * 3;
                for (int x = 0; x < W; ++x) {
                    float fx = (float(x) + 0.5f) * 0.25f - 0.5f;
                    int x0 = int(clampf(std::floor(fx), 0.0f, float(bW - 1)));
                    int x1 = std::min(bW - 1, x0 + 1);
                    float wx = clampf(fx - x0, 0.0f, 1.0f);
                    const int i0 = x0 * 3, i1 = x1 * 3;
                    for (int c = 0; c < 3; ++c) {
                        float a0 = (0.6f * r_y0[i0 + c] + 0.4f * r2_y0[i0 + c]) * (1.0f - wx)
                                 + (0.6f * r_y0[i1 + c] + 0.4f * r2_y0[i1 + c]) * wx;
                        float a1 = (0.6f * r_y1[i0 + c] + 0.4f * r2_y1[i0 + c]) * (1.0f - wx)
                                 + (0.6f * r_y1[i1 + c] + 0.4f * r2_y1[i1 + c]) * wx;
                        float gl = a0 * (1.0f - wy) + a1 * wy;
                        float base = clampf(c_row[x * 3 + c], 0.0f, 1.0f);
                        c_row[x * 3 + c] = 1.0f - (1.0f - base) * (1.0f - clampf(bloom_amt * gl, 0.0f, 1.0f));
                    }
                }
            }
        };
        std::thread tu(up_fn, 0, midH);
        up_fn(midH, H);
        tu.join();
    }

    // 5. Apply vignette, optional fade to bare canvas, and pack to uint8 RGB24 (2 threads)
    {
        size_t mid = npix / 2;
        auto pack_fn = [&](size_t i0, size_t i1) {
            for (size_t i = i0; i < i1; ++i) {
                float vg = vig[i];
                float r = col[i * 3 + 0] * vg;
                float g = col[i * 3 + 1] * vg;
                float b = col[i * 3 + 2] * vg;
                if (fade_amt > 0.0005f) {
                    float m = (1.0f + 0.012f * lo_tex[i]) * (1.0f + 0.02f * wv[i]);
                    r = r * (1.0f - fade_amt) + canvas_r * m * fade_amt;
                    g = g * (1.0f - fade_amt) + canvas_g * m * fade_amt;
                    b = b * (1.0f - fade_amt) + canvas_b * m * fade_amt;
                }
                out_rgb24[i * 3 + 0] = uint8_t(clampf(r, 0.0f, 1.0f) * 255.0f + 0.5f);
                out_rgb24[i * 3 + 1] = uint8_t(clampf(g, 0.0f, 1.0f) * 255.0f + 0.5f);
                out_rgb24[i * 3 + 2] = uint8_t(clampf(b, 0.0f, 1.0f) * 255.0f + 0.5f);
            }
        };
        std::thread tp(pack_fn, 0, mid);
        pack_fn(mid, npix);
        tp.join();
    }
}

}  // extern "C"
