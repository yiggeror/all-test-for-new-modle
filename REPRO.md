# Gate 1 · 从源重建静帧

## 新阶段：Gate 1.5

按 [Round 1](https://github.com/yiggeror/all-test-for-new-modle/blob/0afc93d133023b3952d826f100e82397c6ec6c29/REVIEW_LOG.md) 锁定 320×180。沿用下方环境，静帧另写 `previews/gate_1_5/`；不改首轮产物。四季源文件由 `render_gate15.py` 映射；春景卧猫耳缘保留局部真实采样，夏／冬各自导入本轮的新场景实现。

```bash
export NUMBA_NUM_THREADS=3 OPENBLAS_NUM_THREADS=1
for s in spring summer autumn winter; do
  .venv/bin/python render_gate15.py "$s"
done
.venv/bin/python make_gate15_cards.py
.venv/bin/python verify_gate15.py --write-manifest
(cd previews/gate_1_5 && sha256sum -c SHA256SUMS.txt)
.venv/bin/python check_gate15_geometry.py
```

下面保留原 Gate 1 的技术说明及 A/B 复现入口供核对。

本地提交候选用 [需求版 `473786ad`](https://github.com/yiggeror/all-test-for-new-modle/tree/473786ad563a61531c9c70edd330edb9271f917e)，已有评审规范留在原处。从 [Rainroji `d3fff8c3b87bacff98e64980c987d2ae0bf92959`](https://github.com/yiggeror/Rainroji/tree/d3fff8c3b87bacff98e64980c987d2ae0bf92959/film) 只带回渲染所需的文本实现，原型的电影、音乐、旧静帧和缓存都不进入构建。

## 环境

Linux，Python 3.12；安装 Noto Sans CJK Regular/Bold 和 Noto Serif CJK Regular（路径 `/usr/share/fonts/opentype/noto/`）。原模板的 wqy/arphic 存在时原样使用、缺失时回退至 Noto 简体。为再现当前镜头字形，优先在仅安装 Noto 的同类环境执行。当前四季均使用 Python 3.12.14、requirements.txt 中列出的 Python 包和 Noto 字体。只在安装包时需公网；渲染本身不需要联网。无 FFmpeg、视频合成、音乐依赖。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export NUMBA_NUM_THREADS=3 OPENBLAS_NUM_THREADS=1
.venv/bin/python gate1.py --scene spring --module shots/spring_still.py --out previews/gate_1
.venv/bin/python gate1.py --scene summer --out previews/gate_1
.venv/bin/python gate1.py --scene autumn --module shots/autumn_still.py --out previews/gate_1
.venv/bin/python gate1.py --scene winter --out previews/gate_1
.venv/bin/python make_review_cards.py
.venv/bin/python -m unittest discover -v
.venv/bin/python verify_outputs.py --write-manifest
(cd previews/gate_1 && sha256sum -c SHA256SUMS.txt)
```

`--samples 3` 是每像素 3×3 条抖动射线，`--colors 60` 上限包含人工保留的高光色，均为默认值。每季的相机、时相和抖动强度见 `shots/` 与输出中的 JSON。同景两档用同一色板，预览图最终用精确整数复制；`gate1.py` 不读旧 640×360 缓存或任何旧图。原型的 `run.py` 不用于 Gate 1。色板版 PNG 与原生 PNG 都在 `previews/gate_1/`。四宫格作为缩略展示，精确块检验只针对独立 1080p 净图。

## 文件范围

- 渲染／检查：根目录的 `gate1.py`、`make_review_cards.py`、`check_grid.py`、`verify_outputs.py`、`test_gate1.py`、`requirements.txt`。首轮的四季入口与两个配套世界文件保留在 `shots/`；Gate 1.5 的复现入口、场景文件与输出另存。
- 冻结原型：`prototype/film/engine/*.py`、`prototype/film/scenes/*.py` 为代码依赖。该目录中原 README、WORKFLOW、run.py 留作溯源，不是运行命令。
- 交付：`DEV_STATUS.md`、此页及 `previews/gate_1/`。不包含本地 venv、日志、试机草稿、JIT 缓存或配乐素材。正式发布前不要把审片辅助帧、样板和净图混淆。
