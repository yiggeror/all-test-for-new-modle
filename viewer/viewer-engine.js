import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const DEFAULT_MODEL_URL = '../assets/suzu_final.glb';
const SAMPLE_RATE = 30;
const FACE_TRACK = 'Fcl_';
const CAMERA_FRAME = Object.freeze({
  full: { focus: .495, height: 1.095, width: .69, angle: 0, elevation: .022 },
  half: { focus: .772, height: .57, width: .52, angle: 8, elevation: .022 },
  face: { focus: .870, height: .345, width: .34, angle: 2.5, elevation: .018 },
  back: { focus: .495, height: 1.095, width: .68, angle: 180, elevation: .025 },
});

// Presets from the approved Phase A expression sculpt, evaluated on the actual GLB.
const FACE_PRESET = Object.freeze({
  neutral: {},
  smile: { MTH_Fun: .45, MTH_Up: .20, EYE_Fun: .18, BRW_Fun: .17 },
  laugh: { MTH_Joy: .90, EYE_Fun: .50, BRW_Joy: .43 },
  closed: { MTH_Fun: .68, MTH_Up: .13, EYE_Joy: .85, EYE_Close: .15, BRW_Fun: .22 },
  surprise: { MTH_O: .72, MTH_Small: .68, MTH_U: .09, EYE_Surprised: .65, BRW_Surprised: .58 },
});

const LIGHT_RIG = Object.freeze({
  front: { pos: [-1.15, 2.60, 3.30], key: 1.7672, fill: .86, rim: .93, hemi: 1.14, lift: .30, gain: .94 },
  left: { pos: [-2.72, 2.75, 2.68], key: 2.02, fill: .77, rim: .86, hemi: 1.21, lift: .28 },
  right: { pos: [2.72, 2.75, 2.68], key: 2.02, fill: .77, rim: .86, hemi: 1.21, lift: .28 },
  back: { pos: [-.62, 2.65, -3.13], key: 1.55, fill: 1.40, rim: .89, hemi: 1.37, lift: .41 },
});

function inOptions(object, value) {
  return Object.hasOwn(object, value);
}

function readMorphPrimitives(model) {
  const primitives = [];
  model.traverse((object) => {
    if (!object.isMesh || !object.morphTargetInfluences?.length) return;
    const indices = Object.fromEntries(Object.entries(object.morphTargetDictionary)
      .filter(([name]) => name.includes(FACE_TRACK))
      .map(([name, index]) => [name.slice(name.indexOf(FACE_TRACK) + FACE_TRACK.length), index]));
    if (indices.MTH_Joy !== undefined) {
      primitives.push({ mesh: object, indices, base: object.morphTargetInfluences.slice() });
    }
  });
  return primitives;
}

function surfaceRole(material) {
  const name = material.name.toLowerCase();
  if (name.startsWith('suzu b ')) return 'hair';
  if (name.startsWith('suzu a ')) {
    for (const role of ['mouth', 'iris', 'skin', 'white', 'line', 'brow', 'highlight', 'body']) {
      if (name.includes(role)) return role;
    }
  }
  return 'other';
}

// Runtime showroom pass. Original albedo maps, alpha and vertex data remain
// the source of truth. Trim, stones and patent leather retain their glTF PBR;
// the large fabric/skin/hair surfaces use shallow, two-stage cel lighting.
function studioMaterialFor(original, studio) {
  const role = surfaceRole(original);
  const name = original.name.toLowerCase();
  const pass = role === 'skin' || role === 'body' ? 'skin' : role === 'hair' ? 'hair'
    : ['iris', 'white', 'brow', 'line', 'highlight', 'mouth'].includes(role) ? 'detail'
    : (name.includes('gold') || name.includes('gilt') || name.includes('brass')
        || name.includes('sapphire') || name.includes('shoe')) ? null : 'cloth';
  if (!pass || !original.isMeshStandardMaterial) return original;

  const material = new THREE.MeshBasicMaterial({
    name: original.name,
    color: original.color,
    map: original.map,
    alphaMap: original.alphaMap,
    opacity: original.opacity,
    transparent: original.transparent,
    alphaTest: original.alphaTest,
    side: original.side,
    vertexColors: original.vertexColors,
    depthTest: original.depthTest,
    depthWrite: original.depthWrite,
    forceSinglePass: true,
  });

  if (role === 'body') {
    material.polygonOffset = true;
    material.polygonOffsetFactor = 1.5;
    material.polygonOffsetUnits = 1.5;
  }

  const ramps = {
    skin: `
      vec3 ramp = mix(vec3(.825,.673,.647),vec3(1.008,.989,.992),lightLevel);
      outgoingLight *= ramp * (1.0-(1.0-suzuKeyGain)*sqrt(primaryLevel));
    `,
    hair: `
      vec3 ramp = mix(vec3(.586,.579,.735),vec3(1.009,1.006,1.015),lightLevel);
      float edge = pow(clamp(1.0-dot(shadeN,normalize(suzuView)),0.0,1.0),3.0);
      float rimLevel = smoothstep(.03,.72,dot(shadeN,rimDir));
      outgoingLight = outgoingLight*ramp + vec3(.038,.049,.089)*edge*rimLevel;
    `,
    detail: `
      outgoingLight *= mix(.86,.998,lightLevel);
    `,
    cloth: `
      float edge = pow(clamp(1.0-dot(shadeN,normalize(suzuView)),0.0,1.0),3.5);
      float rimLevel = smoothstep(.04,.82,dot(shadeN,rimDir));
      float fabricKey = smoothstep(.14,.93,dot(shadeN,keyDir))*suzuKeyGain;
      float fabricFill = smoothstep(-.05,.80,dot(shadeN,fillDir))*suzuLift*.67;
      float fabricLevel = fabricKey + (1.0-fabricKey)*fabricFill;
      vec3 ramp = mix(vec3(.48,.51,.64),vec3(1.22,1.24,1.26),fabricLevel);
      outgoingLight *= ramp + vec3(.22,.26,.37)*edge*rimLevel;
    `,
  };

  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, studio);
    shader.vertexShader = shader.vertexShader.replace('#include <common>', `
      #include <common>
      varying vec3 suzuNormal;
      varying vec3 suzuView;
    `).replace('#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )', '#if 1')
      .replace('#include <defaultnormal_vertex>', `
        #include <defaultnormal_vertex>
        suzuNormal = transformedNormal;
      `).replace('#include <project_vertex>', `
        #include <project_vertex>
        suzuView = -mvPosition.xyz;
      `);
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `
      #include <common>
      varying vec3 suzuNormal;
      varying vec3 suzuView;
      uniform vec3 suzuKey;
      uniform vec3 suzuFill;
      uniform vec3 suzuRim;
      uniform float suzuLift;
      uniform float suzuKeyGain;
    `).replace('#include <opaque_fragment>', `
      vec3 shadeN = normalize(suzuNormal) * (gl_FrontFacing ? 1.0 : -1.0);
      vec3 keyDir = normalize((viewMatrix*vec4(suzuKey,0.0)).xyz);
      vec3 fillDir = normalize((viewMatrix*vec4(suzuFill,0.0)).xyz);
      vec3 rimDir = normalize((viewMatrix*vec4(suzuRim,0.0)).xyz);
      float primaryLevel = smoothstep(-.035,.73,dot(shadeN,keyDir))*suzuKeyGain;
      float returnLevel = smoothstep(-.15,.70,dot(shadeN,fillDir))*suzuLift;
      float lightLevel = primaryLevel + (1.0-primaryLevel)*returnLevel;
      ${ramps[pass]}
      #include <opaque_fragment>
    `);
  };
  material.customProgramCacheKey = () => `suzu-studio-${pass}`;
  return material;
}

function clayMaterialFor(original) {
  const role = surfaceRole(original);
  const colors = { mouth: 0x998e99, iris: 0x7c768b, white: 0xe9e5ec, line: 0x746e7e,
    brow: 0x827888, highlight: 0xd0cad7 };
  const isCard = original.transparent;
  const material = new THREE.MeshLambertMaterial({
    color: colors[role] ?? 0xc3c0ca,
    side: original.side,
    map: isCard ? original.map : null,
    alphaTest: isCard ? .28 : 0,
  });
  // An imported decal's map is only a stencil here, not a gray-graded texture.
  if (isCard && original.map) {
    material.onBeforeCompile = (shader) => {
      shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
        #ifdef USE_MAP
          diffuseColor.a *= texture2D(map, vMapUv).a;
        #endif
      `);
    };
    material.customProgramCacheKey = () => 'suzu-clay-alpha';
  }
  return material;
}

function wireMaterial() {
  const material = new THREE.MeshBasicMaterial({
    color: 0x33264e,
    transparent: true,
    opacity: .44,
    depthWrite: false,
    wireframe: true,
    side: THREE.FrontSide,
    forceSinglePass: true,
  });
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>', `
      #include <project_vertex>
      gl_Position.z -= gl_Position.w * 0.00012;
    `);
  };
  material.customProgramCacheKey = () => 'suzu-wire-depth-bias';
  return material;
}

function makeContactShadow(scene) {
  const image = document.createElement('canvas');
  image.width = image.height = 96;
  const ctx = image.getContext('2d');
  if (!ctx) return null;
  const ring = ctx.createRadialGradient(48, 48, 3, 48, 48, 47);
  ring.addColorStop(0, 'rgba(35,30,62,.35)');
  ring.addColorStop(.35, 'rgba(43,36,74,.25)');
  ring.addColorStop(.70, 'rgba(47,40,78,.07)');
  ring.addColorStop(1, 'rgba(47,40,78,0)');
  ctx.fillStyle = ring;
  ctx.fillRect(0, 0, 96, 96);
  const texture = new THREE.CanvasTexture(image);
  texture.colorSpace = THREE.SRGBColorSpace;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(.79, .53), new THREE.MeshBasicMaterial({
    map: texture, transparent: true, depthWrite: false, toneMapped: false,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  mesh.rotation.x = -Math.PI / 2;
  mesh.renderOrder = -1;
  scene.add(mesh);
  return mesh;
}

/**
 * Inspect the frozen character, with render-only lighting and inspection passes.
 * onProgress receives a fraction and a {phase, loaded?, total?} detail.
 * onState receives a snapshot; timeline updates are throttled.
 */
export async function createViewer(canvas, {
  modelUrl = DEFAULT_MODEL_URL,
  onProgress = () => {},
  onState = () => {},
} = {}) {
  if (!(canvas instanceof HTMLCanvasElement)) throw new TypeError('A canvas is required.');
  onProgress(0, { phase: 'loading' });
  const renderer = new THREE.WebGLRenderer({
    canvas, antialias: false, alpha: true, powerPreference: 'high-performance',
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(33, 1, .12, 13);
  camera.position.set(0, .83, 3.5);
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = true;
  orbit.dampingFactor = .15;
  orbit.enablePan = true;
  orbit.enableRotate = true;
  orbit.enableZoom = true;
  orbit.zoomSpeed = .9;
  orbit.rotateSpeed = .78;
  orbit.panSpeed = .8;
  orbit.minDistance = .22;
  orbit.maxDistance = 12;
  orbit.minPolarAngle = .10;
  orbit.maxPolarAngle = Math.PI - .06;
  if (!canvas.hasAttribute('tabindex')) canvas.tabIndex = 0;
  orbit.listenToKeyEvents(canvas);

  const hemi = new THREE.HemisphereLight('#e8e9ff', '#f1cdc6', 1.26);
  const key = new THREE.DirectionalLight('#fff1eb', 2.23);
  const fill = new THREE.DirectionalLight('#e8edff', 1.23);
  const rim = new THREE.DirectionalLight('#cbdcff', 1.08);
  for (const light of [key, fill, rim]) {
    light.target.position.set(0, 1.05, 0);
    scene.add(light, light.target);
  }
  scene.add(hemi);
  const contactShadow = makeContactShadow(scene);
  const studio = {
    suzuKey: {value: new THREE.Vector3()},
    suzuFill: {value: new THREE.Vector3()},
    suzuRim: {value: new THREE.Vector3()},
    suzuLift: {value: 0},
    suzuKeyGain: {value: 1},
  };

  let gltf;
  try {
    gltf = await new GLTFLoader().loadAsync(modelUrl, (event) => {
      const fraction = event.lengthComputable ? event.loaded / event.total : 0;
      onProgress(Math.min(.96, fraction * .96), { phase: 'loading', loaded: event.loaded, total: event.total });
    });
  } catch (error) {
    orbit.dispose();
    renderer.dispose();
    throw error;
  }
  onProgress(.97, { phase: 'preparing' });
  const model = gltf.scene;
  scene.add(model);
  const surfaces = [];
  const bones = new Set();
  const passMaterials = new Map();
  const stagePass = (original) => {
    if (!passMaterials.has(original)) passMaterials.set(original, studioMaterialFor(original, studio));
    return passMaterials.get(original);
  };
  const cardOrder = { iris: 11, line: 12, brow: 13, highlight: 14 };
  model.traverse((object) => {
    if (!object.isMesh) return;
    const slot = object.material;
    const first = Array.isArray(slot) ? slot[0] : slot;
    if (object.isSkinnedMesh) {
      for (const bone of object.skeleton.bones) bones.add(bone);
      // The rest-pose box is not valid for the late wrist, dress and hair motion.
      object.frustumCulled = false;
    }
    const role = surfaceRole(first);
    if (cardOrder[role]) object.renderOrder = cardOrder[role];
    const shaded = Array.isArray(slot) ? slot.map(stagePass) : stagePass(slot);
    object.material = shaded;
    surfaces.push({ object, original: slot, shaded, clay: undefined, wire: undefined,
      card: first.transparent });
  });

  const morphs = readMorphPrimitives(model);
  const rawClip = gltf.animations[0];
  if (!rawClip || !morphs.length) {
    orbit.dispose();
    renderer.dispose();
    throw new Error('The character needs its continuous clip and native face targets.');
  }
  const mixer = new THREE.AnimationMixer(model);
  const action = mixer.clipAction(rawClip);
  action.setLoop(THREE.LoopOnce, 1);
  action.clampWhenFinished = true;
  action.play();
  // The final sample occupies one 30 fps display frame after the last key.
  const duration = Math.round((rawClip.duration + 1 / SAMPLE_RATE) * SAMPLE_RATE) / SAMPLE_RATE;
  const state = {
    ready: true, view: 'full', mode: 'shaded', light: 'front',
    playing: false, time: 0, duration, expression: 'neutral', expressionMode: 'timeline',
    meshCount: surfaces.length, boneCount: bones.size,
    morphTargetCount: Object.keys(morphs[0].indices).length,
  };

  const surfaceMaterials = new Set();
  const originalTextures = new Set();
  for (const surface of surfaces) {
    for (const m of [].concat(surface.original, surface.shaded)) {
      surfaceMaterials.add(m);
      for (const value of Object.values(m)) if (value?.isTexture) originalTextures.add(value);
    }
  }
  const geometries = new Set(surfaces.map(({object}) => object.geometry));
  const clayCache = new Map();
  let commonWire = null;
  let destroyed = false;
  let raf = 0;
  let dirty = false;
  let cameraDirty = false;
  let previousTime = 0;
  let previousNotification = 0;
  let lastWidth = 0;
  let lastHeight = 0;
  let followsPreset = true;
  let manual = null;

  function restoreAuthoredMorphs() {
    if (!manual) return;
    for (const { mesh, base } of morphs) {
      for (let i = 0; i < base.length; i++) mesh.morphTargetInfluences[i] = base[i];
    }
    manual = null;
  }

  function sample(time) {
    restoreAuthoredMorphs();
    action.time = Math.min(time, rawClip.duration);
    mixer.update(0);
  }

  sample(0);
  model.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model, true);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const modelHeight = size.y;
  if (contactShadow) {
    contactShadow.position.set(center.x * .33, bounds.min.y - .001, center.z * .32);
  }

  // Keep the first frame sharp without making small mobile viewports render 3× pixels.
  renderer.setPixelRatio(Math.min(Math.max(window.devicePixelRatio || 1, 1.20), 1.60));

  function getState() {
    const { mesh, indices } = morphs[0];
    const morphWeights = {};
    for (const [name, index] of Object.entries(indices)) {
      const value = mesh.morphTargetInfluences[index];
      if (Math.abs(value) > .0001) morphWeights[name] = value;
    }
    return { ...state, morphWeights, cameraPosition: camera.position.toArray(), orbitTarget: orbit.target.toArray() };
  }

  function notify() {
    previousNotification = performance.now();
    onState(getState());
  }

  function requestFrame() {
    dirty = true;
    if (!destroyed && !raf) raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    if (destroyed) return;
    const dt = previousTime ? Math.max(0, (now - previousTime) / 1000) : 0;
    previousTime = now;
    const animated = state.playing;
    if (animated) {
      state.time = Math.min(state.duration, state.time + dt);
      sample(state.time);
      if (state.time >= state.duration) {
        state.playing = false;
        notify();
      } else if (now - previousNotification > 73) {
        notify();
      }
    }
    const moved = orbit.update(Math.min(.067, dt));
    if (dirty || moved || animated) {
      renderer.render(scene, camera);
      dirty = false;
    }
    if (state.playing || moved || cameraDirty) {
      cameraDirty = false;
      if (!raf) raf = requestAnimationFrame(frame);
    }
  }

  function orbitStart() {
    followsPreset = false;
  }
  function orbitChange() {
    cameraDirty = true;
    requestFrame();
  }
  orbit.addEventListener('start', orbitStart);
  orbit.addEventListener('change', orbitChange);

  function applyFrame(view) {
    const preset = CAMERA_FRAME[view];
    const h = modelHeight * preset.height;
    const w = modelHeight * preset.width;
    const fov = THREE.MathUtils.degToRad(camera.fov);
    const distance = Math.max(h, w / camera.aspect) / (2 * Math.tan(fov / 2)) + size.z * .18;
    const angle = THREE.MathUtils.degToRad(preset.angle);
    const y = bounds.min.y + preset.focus * modelHeight;
    const x = view === 'face' ? 0 : center.x * .42;
    const targetZ = view === 'face' ? bounds.max.z * .22 : center.z * .18;
    orbit.target.set(x, y, targetZ);
    camera.position.set(x + Math.sin(angle) * distance, y + preset.elevation * distance,
      targetZ + Math.cos(angle) * distance);
    orbit.update();
    orbit.saveState();
  }

  function resize() {
    if (destroyed) return;
    const width = Math.max(1, Math.round(canvas.clientWidth));
    const height = Math.max(1, Math.round(canvas.clientHeight));
    if (width === lastWidth && height === lastHeight) return;
    lastWidth = width;
    lastHeight = height;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (followsPreset) applyFrame(state.view);
    requestFrame();
  }

  function setView(view) {
    if (!inOptions(CAMERA_FRAME, view)) return;
    state.view = view;
    followsPreset = true;
    applyFrame(view);
    requestFrame();
    notify();
  }

  function applyLight(name) {
    const preset = LIGHT_RIG[name];
    key.position.set(...preset.pos);
    key.intensity = preset.key;
    fill.position.set(name === 'right' ? -1.73 : 1.73, 1.71, 3.1);
    fill.intensity = preset.fill;
    rim.position.set(name === 'left' ? 1.7 : -1.45, 2.2, name === 'back' ? -2.96 : -2.5);
    rim.intensity = preset.rim;
    hemi.intensity = preset.hemi;
    studio.suzuKey.value.copy(key.position).sub(key.target.position).normalize();
    studio.suzuFill.value.copy(fill.position).sub(fill.target.position).normalize();
    studio.suzuRim.value.copy(rim.position).sub(rim.target.position).normalize();
    studio.suzuLift.value = preset.lift;
    studio.suzuKeyGain.value = preset.gain ?? 1;
  }
  applyLight(state.light);

  function setLight(light) {
    if (!inOptions(LIGHT_RIG, light) || light === state.light) return;
    state.light = light;
    applyLight(light);
    requestFrame();
    notify();
  }

  function wireFor(surface) {
    if (surface.card || surface.wire) return surface.wire;
    commonWire ||= wireMaterial();
    const source = surface.object;
    const overlay = source.clone(false);
    overlay.name = `${source.name} · inspection wire`;
    overlay.material = commonWire;
    overlay.renderOrder = 3;
    overlay.position.set(0, 0, 0);
    overlay.quaternion.identity();
    overlay.scale.set(1, 1, 1);
    overlay.matrix.identity();
    overlay.matrixAutoUpdate = true;
    // Mesh and SkinnedMesh.copy preserve geometry/skeleton. Share, rather than copy,
    // the source's influence array so linework follows the actual expression.
    if (source.morphTargetInfluences) overlay.morphTargetInfluences = source.morphTargetInfluences;
    source.add(overlay);
    surface.wire = overlay;
    return overlay;
  }

  function setMode(mode) {
    if (!['shaded', 'clay', 'wire'].includes(mode) || mode === state.mode) return;
    state.mode = mode;
    for (const surface of surfaces) {
      if (mode === 'clay') {
        if (!surface.clay) {
          const neutral = (source) => {
            if (!clayCache.has(source)) clayCache.set(source, clayMaterialFor(source));
            return clayCache.get(source);
          };
          surface.clay = Array.isArray(surface.original) ? surface.original.map(neutral) : neutral(surface.original);
        }
        surface.object.material = surface.clay;
      } else {
        surface.object.material = surface.shaded;
      }
      if (mode === 'wire') wireFor(surface);
      if (surface.wire) surface.wire.visible = mode === 'wire';
    }
    requestFrame();
    notify();
  }

  function setExpression(expression) {
    if (!inOptions(FACE_PRESET, expression)) return;
    restoreAuthoredMorphs();
    state.playing = false;
    state.expression = expression;
    state.expressionMode = 'manual';
    manual = expression;
    for (const { mesh, indices, base } of morphs) {
      const influences = mesh.morphTargetInfluences;
      for (let i = 0; i < influences.length; i++) {
        base[i] = influences[i];
        influences[i] = 0;
      }
      for (const [name, weight] of Object.entries(FACE_PRESET[expression])) {
        influences[indices[name]] = weight;
      }
    }
    requestFrame();
    notify();
  }

  function useTimeline() {
    state.expression = 'neutral';
    state.expressionMode = 'timeline';
  }

  function seek(seconds) {
    const time = Number(seconds);
    if (!Number.isFinite(time)) return;
    state.time = Math.max(0, Math.min(state.duration, time));
    useTimeline();
    sample(state.time);
    previousTime = performance.now();
    requestFrame();
    notify();
  }

  function setPlaying(playing) {
    const next = Boolean(playing);
    if (next === state.playing) return;
    state.playing = next;
    if (next) {
      if (state.time >= duration - .0001) state.time = 0;
      useTimeline();
      sample(state.time);
      previousTime = performance.now();
    }
    requestFrame();
    notify();
  }

  function destroy() {
    if (destroyed) return;
    destroyed = true;
    if (raf) cancelAnimationFrame(raf);
    observer.disconnect();
    orbit.dispose();
    mixer.stopAllAction();
    mixer.uncacheRoot(model);
    for (const geo of geometries) geo.dispose();
    for (const tex of originalTextures) tex.dispose();
    for (const m of surfaceMaterials) m.dispose();
    for (const m of clayCache.values()) m.dispose();
    commonWire?.dispose();
    if (contactShadow) {
      contactShadow.geometry.dispose();
      contactShadow.material.map.dispose();
      contactShadow.material.dispose();
    }
    for (const skeleton of new Set(surfaces.map(({object}) => object.skeleton).filter(Boolean))) skeleton.dispose();
    renderer.dispose();
  }

  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  resize();
  if (raf) cancelAnimationFrame(raf);
  raf = 0;
  dirty = false;
  cameraDirty = false;
  renderer.render(scene, camera);
  onProgress(1, { phase: 'ready' });
  notify();
  return { setView, setMode, setLight, setExpression, setPlaying, seek, getState,
    reset: () => setView(state.view), destroy };
}
