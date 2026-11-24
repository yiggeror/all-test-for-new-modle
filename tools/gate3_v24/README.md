# Rainroji v2.4 · Gate 3.4 一键重建

在完整项目分支的仓库根目录运行：

    python -m pip install -r tools/gate3_v24/requirements.txt
    python tools/gate3_v24/reproduce.py

使用 Python 3.12、带 libx264 的 FFmpeg 与 ffprobe，预留 2 GB 工作空间。脚本默认从已核验作者站点下载完整 Green Tea MP3，以固定字节数、SHA-256 验证。可选 --music-cache 指向该原曲的本地正版副本，仍强校验；不能用 v2.0 成片 AAC 替代。本目录独立，不改 v2–v2.3 现有构建。必要时 --keep-picture 可保留已核验封装前画面轨。不会覆盖已有 dist 输出。

## 画面

[Round 16](https://github.com/yiggeror/all-test-for-new-modle/blob/1fa86680089be1b6ee8a07dab2a13d865de05dd6/REVIEW_LOG.md) 批准的 [ffd3b67](https://github.com/yiggeror/all-test-for-new-modle/commit/ffd3b67dc2d7a7bf84e9cb58d866ae3b0d0d8d0a) 16 个无损分卷是唯一画面输入。验证清单、每卷和整条母轨 SHA-256；真实解码各660帧，精确核其30fps相位与重复的第二周期；只用同版色表把碰撞为零的 BT.709 键反解回实际 320×180。不使用历史成片、代理或外部原生序列。夏景全部八分卷与已经签收的 v2.3 逐字节一致。

先在原生线性光叠化，每处2.0秒、smoothstep 时间权重，中心在48、96、144秒，首45帧淡入，尾从F5802用114帧相位步长渐黑到F5916。后以6×最近邻升至1920×1080，单次 H.264 High / CRF14 / BT.709 限幅 / faststart。完整5917帧197.233333秒不加时；独审锁定编码前 RGB24 字节和值序。

## 音轨

Purrple Cat《Green Tea》CC BY 4.0，全曲保持 9,466,286 个 48kHz 样本顺序、不截断、不循环。原有环境声与窗边拟音由仓库已有 tools/gate3/gate3_audio.py 重新确定性生成；前段与已审混音设置保留，按 Round 15d 加入冬夜尾部抬升、低通及最后对齐画面的环境音淡出。最终混合由此版 audio_tail.py 完成，AAC-LC 48kHz立体声 256kbps 目标码率、综合约−16 LUFS、真峰不超过−1.5 dBTP。封装只复制新混音轨，校验所有9247个包的配置、实际载荷、时间戳、尾样本和 priming 全等；最终视音同长为5917/30秒。[保留署名和具体尾声说明](../../CREDITS.md)。

正式候审路径 **dist/Rainroji_Lofi_V2.4_1080p.mp4**；实际解码及校验位于 dist/gate3_v24_qa/。完整可听的尾声对比与音乐/环境顺序量化表见 [Gate 3.4 审片证据](../../previews/gate_3_4/)。

参考构建：Debian x86_64，Python 3.12.14，NumPy 2.3.5，Pillow 13.0.0，SciPy 1.17.0，FFmpeg 7.1.5-0+deb13u1，x264 core 164 r3108 31e19f9。其他 x264/FFmpeg 编译版本可产生不同压缩文件 SHA，原生画面、正式原曲、锁定时间与验证规格不变。本地回归：

    python -m unittest discover -s tools/gate3_v24
