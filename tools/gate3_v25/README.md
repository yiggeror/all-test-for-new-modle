# Rainroji v2.5 · Gate 3.5 终版

从审批后的 17 份无损分卷重建真画面，从已发布的 v2.4 **直接复制**原 AAC。不给旧整片的画面或压缩审片代理作输入，不渲染任何新音效，不需要无损 NPY、音乐源或剪辑软件。

## 重建

从包含 [Round 20 正式审批](https://github.com/yiggeror/all-test-for-new-modle/blob/de0190b398d70b2cf39d82db9fe5a674fff45137/REVIEW_LOG.md#L807-L845) 的项目检出完整的 `previews/gate_2_5/lossless_parts/`：

```sh
python -m pip install -r tools/gate3_v25/requirements.txt
python tools/gate3_v25/reproduce.py
```

需要 Python 3.12+ 和 PATH 中带 libx264 的 FFmpeg / ffprobe。实测 Python 3.12.14、NumPy 2.3.5、Pillow 13.0.0、FFmpeg 7.1.5-0+deb13u1。输出到仓库的 `dist/Rainroji_Lofi_V2.5_1080p.mp4` 和 `dist/gate3_v25_qa/`，存在则拒绝覆盖。临时文件约 800 MB 峰值，无需存储 5917 帧 RGB 流。若要额外保留只含画面的编码轨，可传 `--keep-picture`。

默认只联网取 [GitHub 正式 v2.4 发布件](https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.4-rainroji-lofi-1080p/Rainroji_Lofi_V2.4_1080p.mp4)，不登录。若 CI/本机已下载，可传 `--v24-release-cache /path/to/Rainroji_Lofi_V2.4_1080p.mp4` 或设置 `RAINROJI_V24_RELEASE_CACHE`；无论用哪条路线同样核对 **132,852,726 字节 / a9870ce471487b76b68c93eb779a075182e5d1b28b3e18d145aae99f480d0687**，其他版本不得代替。输出与网络地址无关，音频源只映射第 1 份可用音轨。

## 画面与声音锁

- 审批对象 `6ef7236da05b81d50b74f5f403881943dea10afb` 的实际清单含 **春 1 + 夏 8 + 秋 2 + 冬 6 = 17 份**。Round 20 正文的「16」为计数差；所有 17 份、合计容器与固定清单逐个验长度/哈希，不能少读秋季最后一份。
- 每季解码 660 帧，检查时间戳、双周相等，再从真实无损 YUV 原生格恢复锁定项目色板 RGB。四季列表并不携带原画面；只保存有限色彩映射和验证指纹，不在普通 YUV→RGB 转换中引入舍入误差。
- 沿用 v2.4 的 48/96/144 s 线性光 smoothstep 叠化各 2.0 s，1.5 s 淡入、193.4–197.2 s 尾淡。以 320×180 RGB 合成，6× 整数最近邻送 1920×1080 H.264 High/CRF 14/BT.709 限幅矩阵并 faststart；精确 5,917 帧 @ 30 fps。实际送编码器 5917 帧整流和七个时间域逐段验 SHA。夏 F1470–2850、冬 F4350–5916 的编码前版本逐像素等于已验收 v2.4；三处叠化的内部帧纳入改好的春/秋。
- 1× 画面只编码一次。音频用 `-c:a copy`，逐包验 9,247 个 AAC-LC 载荷、PTS、DTS、包时长、AudioSpecificConfig、首包 priming 和末包有效段。同样的 9,467,200 个 48kHz 样点时长保留 v2.4 尾声雪风收尾。
- 运行中会完整解码两轨并核实际帧数、时钟与响度，生成未叠字的全幅实解静帧。不同 FFmpeg/libx264 构建最后压缩容器的 SHA 可能不同；批准分卷、编码前 RGB、音包及时间锁不变。不用本地 MP4 SHA 判其他工具链画面是否通过。

```sh
python -m unittest discover -s tools/gate3_v25 -v
```
