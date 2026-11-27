import { createViewer } from './viewer-engine.js';

const $ = (selector) => document.querySelector(selector);
const controls = [...document.querySelectorAll('.controls button, .controls input')];
const timeline = $('#timeline'), play = $('#play'), retry = $('#retry');
const labels = {view:{full:'全身',half:'半身',face:'脸部特写',back:'背面'},mode:{shaded:'二次元着色',clay:'哑光灰模',wire:'线框叠加'}};
const handlers = {view:'setView',mode:'setMode',light:'setLight',expression:'setExpression'};
let viewer, following = true, playing = false;
let state = {view:'full',mode:'shaded',light:'front',expression:'neutral',time:0,duration:11.4,playing:false};
for (const el of controls) el.disabled = true;
for (const axis of Object.keys(handlers)) {
 for (const btn of document.querySelectorAll(`[data-${axis}]`)) {
  btn.addEventListener('click', () => {
   const value = btn.dataset[axis];
   viewer[handlers[axis]](value);
   synchronize({[axis]:value});
  });
 }
}
play.addEventListener('click', () => { viewer.setPlaying(!playing); });
timeline.addEventListener('pointerdown', () => {following = false;});
for (const event of ['pointerup','pointercancel','change','blur']) timeline.addEventListener(event, () => { following = true; });
timeline.addEventListener('input', () => {
 const time = Number(timeline.value);
 viewer.seek(time);
 synchronize({time});
});
retry.addEventListener('click', () => location.reload());

function synchronize(patch = {}) {
 state = {...state,...patch};
 for (const axis of Object.keys(handlers)) {
  for (const btn of document.querySelectorAll(`[data-${axis}]`)) {
   btn.setAttribute('aria-pressed', String(btn.dataset[axis] === state[axis]));
  }
 }
 const v = labels.view[state.view] ?? labels.view.full, m = labels.mode[state.mode] ?? labels.mode.shaded;
 $('#view-label').textContent = `${v} / ${m}`;
 if (playing !== state.playing || !play.dataset.initialized) {
  playing = Boolean(state.playing);
  play.dataset.initialized = 'yes';
  play.setAttribute('aria-label', playing ? '暂停' : '播放');
  $('#play-icon').setAttribute('d', playing ? 'M7 5h4v14H7zm7 0h4v14h-4z' : 'M8 5v14l11-7Z');
 }
 const seconds = Number(state.duration);
 if (Number.isFinite(seconds) && seconds > 0) {
  timeline.max = seconds.toFixed(2);
  $('#duration').value = seconds.toFixed(2);
 }
 const t = Number(state.time);
 if (Number.isFinite(t)) {
  if (following) timeline.value = String(t);
  $('#now').value = t.toFixed(2);
 }
}

try {
 if (location.protocol === 'file:') throw new Error('请用本地服务打开。');
 viewer = await createViewer($('#scene'), {
  modelUrl: '../assets/suzu_final.glb',
  onProgress(progress) {
   const v = typeof progress === 'number' ? progress :
    (progress?.total ? progress.loaded / progress.total : progress?.fraction);
   if (Number.isFinite(v) && v >= 0) {
    const percent = Math.min(100, Math.round(v > 1 ? v : v * 100));
    $('#load-detail').textContent = percent >= 100 ? '正在初始化 3D 画布' : `正在读取星野铃 · ${percent}%`;
   }
  },
  onState: synchronize
 });
 for (const el of controls) el.disabled = false;
 synchronize(viewer.getState());
 $('#loading').hidden = true;
 $('.ready').dataset.state = 'ready';
 $('#status').textContent = '模型已加载';
 if (new URLSearchParams(location.search).has('check')) {
  window.suzuViewer = viewer;
 }
} catch (err) {
 $('#load-detail').textContent = '无法打开 3D 检视器。请用本地启动器打开，并确认浏览器已启用 WebGL。';
 $('#status').textContent = '未能加载';
 $('.ready').dataset.state = 'err';
 retry.hidden = false;
 console.error(err);
}
