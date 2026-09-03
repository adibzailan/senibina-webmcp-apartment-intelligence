/** Three.js architectural canvas: GLB scene with opacity tokens from node extras, edges always
 *  drawn, sensor heatmap quads, sun vector, camera presets. */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export const OPACITY: Record<string, number> = { context: 0.16, tower: 0.28, home: 1.0, glass: 0.35 };
const COLOURS: Record<string, number> = { context: 0xd9ddd5, tower: 0xe7e1d4, home: 0xfbfaf6, glass: 0x8fb7c9 };
const RAMP = ["#183f5a", "#2b8c86", "#e3c946", "#c8472d"].map((c) => new THREE.Color(c));

export function rampColour(t: number): THREE.Color {
  const x = Math.max(0, Math.min(1, t)) * (RAMP.length - 1);
  const i = Math.min(Math.floor(x), RAMP.length - 2);
  return RAMP[i].clone().lerp(RAMP[i + 1], x - i);
}

export class Viewer {
  renderer: THREE.WebGLRenderer;
  scene = new THREE.Scene();
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  model: THREE.Group | null = null;
  heat: THREE.Group | null = null;
  sun: THREE.Group | null = null;
  slots: THREE.Group | null = null;
  private slotMeshes: THREE.Mesh[] = [];
  private onPick: ((id: string) => void) | null = null;
  private downAt: [number, number] | null = null;
  home = new THREE.Box3();
  tower = new THREE.Box3();
  precinct = new THREE.Box3();
  private raf = 0;
  private ro: ResizeObserver;
  basemap: THREE.Mesh | null = null;
  massing = true;
  private labels: THREE.Group | null = null;
  onFrame: ((azimuthDeg: number) => void) | null = null;
  private gizmo = new THREE.Scene();
  private gizmoCam = new THREE.OrthographicCamera(-2.1, 2.1, 2.1, -2.1, 0.1, 20);
  gizmoSize = 104; // CSS px, drawn in the top-right corner of the canvas

  constructor(public el: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true, logarithmicDepthBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0xfbfaf6, 1);
    el.appendChild(this.renderer.domElement);
    this.camera = new THREE.PerspectiveCamera(38, 1, 0.5, 5000);
    this.camera.up.set(0, 0, 1);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = false;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0xb0b0a0, 1.1));
    const d = new THREE.DirectionalLight(0xffffff, 0.8); d.position.set(-200, -300, 400); this.scene.add(d);
    // ground layers are spaced apart so they never fight for the same depth
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.MeshBasicMaterial({ color: 0xf5f2e9 }));
    ground.position.z = -1.0; ground.renderOrder = -2; this.scene.add(ground);
    const grid = new THREE.GridHelper(1200, 24, 0xb9b7ae, 0xe2e0d8); grid.rotation.x = Math.PI / 2; grid.position.z = -0.6; grid.renderOrder = -1; this.scene.add(grid);
    this.buildGizmo();
    const dom = this.renderer.domElement;
    dom.addEventListener("pointerdown", (e) => { this.downAt = [e.clientX, e.clientY]; });
    dom.addEventListener("pointerup", (e) => {
      if (!this.downAt || !this.onPick || !this.slotMeshes.length) return;
      const moved = Math.hypot(e.clientX - this.downAt[0], e.clientY - this.downAt[1]);
      this.downAt = null;
      if (moved > 4) return;
      const r = dom.getBoundingClientRect();
      const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      const rc = new THREE.Raycaster(); rc.setFromCamera(ndc, this.camera);
      const hit = rc.intersectObjects(this.slotMeshes, false)[0];
      if (hit) this.onPick((hit.object as any).userData.slotId);
    });
    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(el);
    this.resize();
    this.loop();
  }

  resize() {
    const w = Math.max(1, this.el.clientWidth), h = Math.max(1, this.el.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
  }

  private loop = () => {
    this.raf = requestAnimationFrame(this.loop);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.renderGizmo();
    if (this.onFrame) {
      const d = new THREE.Vector3(); this.camera.getWorldDirection(d);
      this.onFrame((Math.atan2(d.x, d.y) * 180) / Math.PI); // compass bearing the camera looks toward, 0 = north (+y)
    }
  };

  /** OpenStreetMap raster tiles as a muted ground plane. Browser-side fetch only, with attribution. */
  async loadBasemap(lon: number, lat: number, zoom = 17, radius = 3, opacity = 0.55): Promise<void> {
    const n = 2 ** zoom, T = 256;
    const px = ((lon + 180) / 360) * n * T;
    const latR = (lat * Math.PI) / 180;
    const py = ((1 - Math.log(Math.tan(latR) + 1 / Math.cos(latR)) / Math.PI) / 2) * n * T;
    const tx = Math.floor(px / T), ty = Math.floor(py / T);
    const mpp = (156543.03392 * Math.cos(latR)) / n;
    const size = (2 * radius + 1) * T;
    const canvas = document.createElement("canvas"); canvas.width = size; canvas.height = size;
    const g = canvas.getContext("2d")!; g.fillStyle = "#f5f2e9"; g.fillRect(0, 0, size, size);
    const loads: Promise<void>[] = [];
    for (let dy = -radius; dy <= radius; dy++) for (let dx = -radius; dx <= radius; dx++) {
      const img = new Image(); img.crossOrigin = "anonymous";
      loads.push(new Promise<void>((res) => { img.onload = () => { g.drawImage(img, (dx + radius) * T, (dy + radius) * T); res(); }; img.onerror = () => res(); }));
      img.src = `https://tile.openstreetmap.org/${zoom}/${tx + dx}/${ty + dy}.png`;
    }
    await Promise.all(loads);
    // desaturate toward paper so the drawing stays the lead image
    g.globalCompositeOperation = "saturation"; g.fillStyle = "hsl(0,0%,50%)"; g.fillRect(0, 0, size, size);
    g.globalCompositeOperation = "source-over";
    const tex = new THREE.CanvasTexture(canvas); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    const metres = size * mpp;
    // world position of the mosaic centre relative to the origin (x east, y north)
    const cxPx = (tx - radius) * T + size / 2, cyPx = (ty - radius) * T + size / 2;
    const cx = (cxPx - px) * mpp, cy = -(cyPx - py) * mpp;
    if (this.basemap) this.scene.remove(this.basemap);
    this.basemap = new THREE.Mesh(new THREE.PlaneGeometry(metres, metres), new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity, depthWrite: false }));
    this.basemap.position.set(cx, cy, -0.2); this.basemap.renderOrder = 0;
    this.scene.add(this.basemap);
  }

  setBasemapVisible(v: boolean) { if (this.basemap) this.basemap.visible = v; }

  /** Room name tags floating above each room, always facing the camera. */
  setRoomLabels(labels: { id: string; text: string; x: number; y: number; z: number }[]) {
    if (this.labels) { this.scene.remove(this.labels); this.labels = null; }
    if (!labels.length) return;
    const g = new THREE.Group();
    for (const l of labels) {
      const c = document.createElement("canvas"); const ctx = c.getContext("2d")!;
      ctx.font = "500 40px Inter, system-ui, sans-serif";
      const w = Math.ceil(ctx.measureText(l.text).width) + 40; c.width = w; c.height = 64;
      ctx.fillStyle = "rgba(251,250,246,0.92)"; ctx.fillRect(0, 0, w, 64);
      ctx.strokeStyle = "#18211d"; ctx.lineWidth = 3; ctx.strokeRect(1.5, 1.5, w - 3, 61);
      ctx.font = "500 40px Inter, system-ui, sans-serif"; ctx.fillStyle = "#18211d"; ctx.textBaseline = "middle"; ctx.fillText(l.text, 20, 34);
      const tex = new THREE.CanvasTexture(c); tex.anisotropy = 4;
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
      const h = 0.55; sp.scale.set((w / 64) * h, h, 1); sp.position.set(l.x, l.y, l.z); sp.renderOrder = 20;
      g.add(sp);
    }
    this.labels = g; this.scene.add(g);
  }

  /** Massing on or off. Off keeps only faint edges of the tower and context so the apartment and its heat reads clean. */
  setMassingVisible(v: boolean) {
    this.massing = v;
    this.model?.traverse((o: any) => {
      if (!o.isMesh || o.userData.token === undefined) return;
      const t: string = o.userData.token;
      if (t === "home" || t === "glass") return;
      o.material.opacity = v ? OPACITY[t] : 0.0; o.material.visible = v;
      o.children.forEach((c: any) => { if (c.isLineSegments) c.material.opacity = v ? (t === "context" ? 0.18 : 0.4) : (t === "context" ? 0.06 : 0.16); });
    });
  }

  dispose() { cancelAnimationFrame(this.raf); this.ro.disconnect(); this.renderer.dispose(); }

  async loadGlb(url: string): Promise<void> {
    const gltf = await new GLTFLoader().loadAsync(url);
    if (this.model) this.scene.remove(this.model);
    this.model = gltf.scene;
    this.home.makeEmpty(); this.tower.makeEmpty(); this.precinct.makeEmpty();
    this.model.traverse((o: any) => {
      if (!o.isMesh) return;
      const extras = o.userData || o.parent?.userData || {};
      const token: string = extras.opacity_token || "context";
      const alpha = OPACITY[token];
      o.material = new THREE.MeshLambertMaterial({ color: COLOURS[token], transparent: alpha < 1, opacity: alpha, depthWrite: alpha >= 1, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: token === "home" ? 0 : 1, polygonOffsetUnits: token === "home" ? 0 : 1 });
      o.renderOrder = alpha < 1 ? 1 : 2; o.userData.token = token;
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 30), new THREE.LineBasicMaterial({ color: token === "home" ? 0x18211d : 0x5f665f, transparent: true, opacity: token === "context" ? 0.18 : token === "tower" ? 0.4 : 0.9 }));
      edges.renderOrder = 3; o.add(edges);
      const box = new THREE.Box3().setFromObject(o);
      this.precinct.union(box);
      if (token === "tower") this.tower.union(box);
      if (token === "home" || token === "glass") this.home.union(box);
    });
    if (!this.massing) this.setMassingVisible(false);
    this.scene.add(this.model);
  }

  setHeat(result: any | null, mode: "radiation" | "solar_access" | "shadow", date: string, hour: number) {
    if (this.heat) { this.scene.remove(this.heat); this.heat = null; }
    if (!result) return;
    const s = result.sensors; const sp = s.grid.spacing_m;
    let values: number[]; let vmin = 0, vmax = 1;
    if (mode === "radiation") { values = result.radiation.sensor_kwh_m2; vmax = Math.max(1e-6, result.radiation.max); }
    else if (mode === "solar_access") { const rec = result.solar_access[date] || Object.values(result.solar_access)[0]; values = rec ? rec.sun_hours : []; vmax = Math.max(1, ...values); }
    else { const inst = this.nearestInstant(result, date, hour); values = inst ? inst.lit_packed.split("").map((c: string) => (c === "1" ? 1 : 0)) : []; vmax = 1; }
    const g = new THREE.Group();
    const geo = new THREE.PlaneGeometry(sp * 0.96, sp * 0.96);
    const mesh = new THREE.InstancedMesh(geo, new THREE.MeshBasicMaterial({ vertexColors: false, side: THREE.DoubleSide }), s.xyz.length);
    const m = new THREE.Matrix4();
    // orient quads with the unit frame: derive rotation from the first two sensors in a row
    const yaw = this.unitYaw(result);
    for (let i = 0; i < s.xyz.length; i++) {
      const [x, y, z] = s.xyz[i];
      m.makeRotationZ(yaw); m.setPosition(x, y, z - s.grid.offset_m + 0.02);
      mesh.setMatrixAt(i, m);
      const v = values[i] ?? 0;
      mesh.setColorAt(i, mode === "shadow" ? (v ? new THREE.Color("#f2c230") : new THREE.Color("#45534d")) : rampColour((v - vmin) / (vmax - vmin)));
    }
    mesh.instanceMatrix.needsUpdate = true; if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.renderOrder = 4;
    g.add(mesh);
    this.heat = g; this.scene.add(g);
  }

  private unitYaw(result: any): number {
    const s = result.sensors;
    for (let i = 1; i < s.xyz.length; i++) if (s.row[i] === s.row[0] && s.col[i] === s.col[0] + 1) return Math.atan2(s.xyz[i][1] - s.xyz[0][1], s.xyz[i][0] - s.xyz[0][0]);
    return 0;
  }

  nearestInstant(result: any, date: string, hour: number) {
    const [mm, dd] = date.split("-").map(Number);
    let best: any = null, bd = 1e9;
    for (const i of result.shadow.instants) { const d = Math.abs(i.month - mm) * 31 + Math.abs(i.day - dd) + Math.abs(i.hour - hour) / 24; if (d < bd) { bd = d; best = i; } }
    return best;
  }

  setSun(result: any | null, date: string, hour: number) {
    if (this.sun) { this.scene.remove(this.sun); this.sun = null; }
    if (!result) return;
    const inst = this.nearestInstant(result, date, hour);
    if (!inst || !inst.is_up) return;
    const c = this.home.isEmpty() ? new THREE.Vector3() : this.home.getCenter(new THREE.Vector3());
    const v = new THREE.Vector3(...inst.vector).normalize();
    const from = c.clone().sub(v.clone().multiplyScalar(120));
    const g = new THREE.Group();
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([from, c]), new THREE.LineBasicMaterial({ color: 0xf2c230 })));
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(2.5, 12, 8), new THREE.MeshBasicMaterial({ color: 0xf2c230 })); sphere.position.copy(from); g.add(sphere);
    this.sun = g; this.scene.add(g);
  }

  /** Draw pickable slot outlines at one storey. Each slot: id, corners [[x,y]x4] in world XY, z. */
  setSlots(slots: { id: string; corners: [number, number][]; z: number }[], selectedId: string | null, onPick: ((id: string) => void) | null) {
    if (this.slots) { this.scene.remove(this.slots); this.slots = null; this.slotMeshes = []; }
    this.onPick = onPick;
    if (!slots.length) return;
    const g = new THREE.Group();
    for (const s of slots) {
      const pts = s.corners.map(([x, y]) => new THREE.Vector3(x, y, s.z + 0.05));
      const selected = s.id === selectedId;
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([...pts, pts[0]]), selected ? new THREE.LineBasicMaterial({ color: 0xc8472d, linewidth: 2 }) : new THREE.LineDashedMaterial({ color: 0x18211d, dashSize: 0.6, gapSize: 0.4, transparent: true, opacity: 0.9 }));
      (line.material as THREE.Material).depthTest = false; line.computeLineDistances(); line.renderOrder = 6; g.add(line);
      const shape = new THREE.Shape(s.corners.map(([x, y]) => new THREE.Vector2(x, y)));
      const fill = new THREE.Mesh(new THREE.ShapeGeometry(shape), new THREE.MeshBasicMaterial({ color: selected ? 0xc8472d : 0x8fa08f, transparent: true, opacity: selected ? 0.5 : 0.35, depthWrite: false, depthTest: false, side: THREE.DoubleSide }));
      fill.position.z = s.z + 0.04; fill.renderOrder = 5; (fill as any).userData.slotId = s.id;
      this.slotMeshes.push(fill); g.add(fill);
    }
    this.slots = g; this.scene.add(g);
  }

  preset(name: "precinct" | "tower" | "home" | "plan" | "north" | "reset", focus: "home" | "tower" = "home") {
    const pick = (...boxes: THREE.Box3[]) => boxes.find((b) => !b.isEmpty());
    const homeFirst = focus === "home" ? [this.home, this.tower, this.precinct] : [this.tower, this.precinct];
    const box = name === "precinct" ? pick(this.precinct) : name === "tower" || name === "north" ? pick(this.tower, this.precinct) : pick(...homeFirst);
    if (!box) return;
    const c = box.getCenter(new THREE.Vector3()); const size = box.getSize(new THREE.Vector3());
    const radius = size.length() / 2;
    this.camera.fov = name === "plan" ? 12 : 38; // a long lens for the plan so towers do not splay
    const fit = radius / Math.sin((this.camera.fov * Math.PI) / 360) * 1.05; // distance that fits the bounding sphere
    if (name === "plan") {
      const h = Math.max(30, fit * 0.9);
      this.camera.position.set(c.x, c.y - 0.001 * h, box.max.z + h);
    } else if (name === "north") {
      this.camera.position.set(c.x, c.y - fit * 0.85, c.z + fit * 0.5); // south of the target, looking north
    } else {
      this.camera.position.set(c.x - fit * 0.55, c.y + fit * 0.55, c.z + fit * 0.4); // from the north-west
    }
    this.controls.target.copy(c); this.camera.near = 0.5; this.camera.far = Math.max(2000, fit * 10); this.camera.updateProjectionMatrix(); this.controls.update();
  }

  /** A small three-dimensional compass: north arrow, east and west ticks, and an up post, sharing the main camera's rotation. */
  private buildGizmo() {
    const g = this.gizmo;
    g.add(new THREE.HemisphereLight(0xffffff, 0x9a9a90, 1.4));
    const disc = new THREE.Mesh(new THREE.CircleGeometry(1.75, 48), new THREE.MeshBasicMaterial({ color: 0xfbfaf6, transparent: true, opacity: 0.85, depthWrite: false }));
    (disc as any).isBackdrop = true; disc.renderOrder = -1; g.add(disc);
    const ring = new THREE.Mesh(new THREE.RingGeometry(1.5, 1.55, 64), new THREE.MeshBasicMaterial({ color: 0xb9b7ae, side: THREE.DoubleSide }));
    g.add(ring);
    const tick = (ang: number, len: number, colour: number) => {
      const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 1.5 - len, 0), new THREE.Vector3(0, 1.5, 0)]);
      const l = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: colour })); l.rotation.z = ang; g.add(l);
    };
    for (let i = 0; i < 16; i++) tick((i * Math.PI) / 8, i % 4 === 0 ? 0.3 : 0.14, 0x8d8b83);
    // north arrow (red), south stub (muted)
    const red = new THREE.MeshLambertMaterial({ color: 0xc8472d }), mute = new THREE.MeshLambertMaterial({ color: 0x5f665f }), ink = new THREE.MeshLambertMaterial({ color: 0x18211d });
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.0, 12), red); shaft.position.y = 0.5; g.add(shaft);
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.45, 16), red); head.position.y = 1.22; g.add(head);
    const south = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.9, 12), mute); south.position.y = -0.45; g.add(south);
    // east and west bars
    const ew = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.2, 12), mute); ew.rotation.z = Math.PI / 2; g.add(ew);
    // up post with a small cap, so tilt reads at a glance
    const up = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 1.1, 12), ink); up.rotation.x = Math.PI / 2; up.position.z = 0.55; g.add(up);
    const cap = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 12), ink); cap.position.z = 1.1; g.add(cap);
    const label = (text: string, x: number, y: number, z: number, colour: string, size = 0.5) => {
      const c = document.createElement("canvas"); c.width = 128; c.height = 128; const cx = c.getContext("2d")!;
      cx.font = "600 84px Inter, system-ui, sans-serif"; cx.textAlign = "center"; cx.textBaseline = "middle"; cx.fillStyle = colour; cx.fillText(text, 64, 68);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthTest: false }));
      sp.position.set(x, y, z); sp.scale.set(size, size, 1); g.add(sp);
    };
    label("N", 0, 1.95, 0, "#c8472d", 0.6); label("S", 0, -1.95, 0, "#5f665f"); label("E", 1.95, 0, 0, "#5f665f"); label("W", -1.95, 0, 0, "#5f665f");
    label("up", 0, 0, 1.5, "#18211d", 0.45);
    this.gizmoCam.up.set(0, 0, 1);
  }

  private renderGizmo() {
    const w = this.el.clientWidth, h = this.el.clientHeight, s = this.gizmoSize, pad = 10;
    if (w < s * 2 || h < s * 2) return;
    const r = this.renderer;
    // same rotation as the main camera, looking at the gizmo origin from 6 units away
    const dir = new THREE.Vector3().subVectors(this.camera.position, this.controls.target).normalize();
    this.gizmoCam.position.copy(dir.multiplyScalar(6)); this.gizmoCam.lookAt(0, 0, 0);
    // the paper disc always faces the viewer
    this.gizmo.children.forEach((c) => { if ((c as any).isBackdrop) c.quaternion.copy(this.gizmoCam.quaternion); });
    r.autoClear = false; r.setScissorTest(true);
    r.setViewport(w - s - pad, h - s - pad, s, s); r.setScissor(w - s - pad, h - s - pad, s, s);
    r.clearDepth(); r.render(this.gizmo, this.gizmoCam);
    r.setScissorTest(false); r.setViewport(0, 0, w, h); r.autoClear = true;
  }

  snapshot(): string { this.renderer.render(this.scene, this.camera); this.renderGizmo(); return this.renderer.domElement.toDataURL("image/png"); }
}
