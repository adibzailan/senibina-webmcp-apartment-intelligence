import * as THREE from 'three'
import { frameBounds } from './camera'

const TARGET = '87'
const seasonal = ['#d6a928', '#d9772b', '#5b8f85', '#c8472d']

function buildingMesh(building, presentation) {
  const shape = new THREE.Shape(building.footprint.map(([x, y]) => new THREE.Vector2(x, -y)))
  const geometry = new THREE.ExtrudeGeometry(shape, { depth: building.height_m, bevelEnabled: false })
  geometry.rotateX(-Math.PI / 2)
  const quietContext = ['solar_access', 'radiation', 'site_export'].includes(presentation.analysis) && building.block !== TARGET
  const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: building.block === TARGET ? '#d8d3c7' : '#fbfaf6', roughness: .9,
    transparent: quietContext, opacity: quietContext ? .1 : 1, depthWrite: !quietContext }))
  mesh.userData.kind = building.block === TARGET ? 'tower' : 'context'
  if (building.block === TARGET) {
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 24), new THREE.LineBasicMaterial({ color: '#5f665f', transparent: true, opacity: .55 }))
    mesh.add(edges)
  }
  return mesh
}

export function homeDescriptor(context, study) {
  if (!context || !study) return null
  const target = context.buildings.find(building => building.address === study.address || building.block === TARGET)
  if (!target) return null
  const xs = target.footprint.map(point => point[0]), ys = target.footprint.map(point => point[1])
  const facade = study.proposal.facade
  const verticalFacade = facade === 'east' || facade === 'west'
  const factor = { left: .25, centre: .5, right: .75 }[study.proposal.position] ?? .5
  const span = verticalFacade ? [Math.min(...ys), Math.max(...ys)] : [Math.min(...xs), Math.max(...xs)]
  const along = span[0] + (span[1] - span[0]) * factor
  const fixed = facade === 'east' ? Math.max(...xs) + .12 : facade === 'west' ? Math.min(...xs) - .12 : facade === 'north' ? Math.max(...ys) + .12 : Math.min(...ys) - .12
  const base = (study.storey - 1) * 3 + study.proposal.sill_height
  const centre = [verticalFacade ? fixed : along, base + study.proposal.window_height / 2, verticalFacade ? -along : -fixed]
  return { target, facade, centre, verticalFacade, base, along, fixed }
}

function addGrid(group, descriptor, study, values, colour) {
  for (let row = 0; row < 8; row++) for (let col = 0; col < 16; col++) {
    const value = values[row * 16 + col] ?? 0
    const cell = new THREE.Mesh(new THREE.PlaneGeometry(study.proposal.window_width / 16 * .92, study.proposal.window_height / 8 * .84), new THREE.MeshBasicMaterial({ color: colour(value, values), side: THREE.DoubleSide, depthTest: false }))
    cell.renderOrder = 12
    const along = descriptor.along - study.proposal.window_width / 2 + study.proposal.window_width * (col + .5) / 16
    cell.position.set(descriptor.verticalFacade ? descriptor.fixed : along, descriptor.base + study.proposal.window_height * (row + .5) / 8, descriptor.verticalFacade ? -along : -descriptor.fixed)
    if (descriptor.verticalFacade) cell.rotation.y = Math.PI / 2
    group.add(cell)
  }
}

function addHome(scene, context, study, result, presentation) {
  const d = homeDescriptor(context, study)
  if (!d) return null
  const group = new THREE.Group(); group.userData.kind = 'home'
  const confirmed = study.state === 'ready' || study.state === 'complete' || Boolean(study.confirmation)
  const zone = new THREE.Mesh(new THREE.PlaneGeometry(study.proposal.width, 3), new THREE.MeshBasicMaterial({ color: '#c8472d', transparent: true, opacity: confirmed ? .3 : .08, wireframe: !confirmed, side: THREE.DoubleSide, depthTest: false }))
  zone.position.fromArray([d.centre[0], d.base + 1.5, d.centre[2]])
  if (d.verticalFacade) zone.rotation.y = Math.PI / 2
  zone.renderOrder = 10; group.add(zone)
  if (result && presentation.analysis === 'radiation') {
    const values = result.radiation.sensor_values_kwh_m2, min = Math.min(...values), max = Math.max(...values)
    addGrid(group, d, study, values, value => new THREE.Color().setHSL((205 - ((value - min) / Math.max(1, max - min)) * 193) / 360, .62, .48))
  } else if (result && presentation.analysis === 'solar_access') {
    const values = result.solar_access[presentation.solarDate]?.sensor_hours || []
    const max = Math.max(1, ...values)
    addGrid(group, d, study, values, value => new THREE.Color().lerpColors(new THREE.Color('#183f5a'), new THREE.Color('#f2c230'), value / max))
  } else if (result && presentation.analysis === 'shadow') {
    const values = result.shadow.samples.find(sample => sample.time === presentation.shadowTime)?.sensor_values || []
    addGrid(group, d, study, values, value => value ? '#f2c230' : '#45534d')
  } else {
    const geometry = new THREE.PlaneGeometry(study.proposal.window_width, study.proposal.window_height)
    const material = confirmed ? new THREE.MeshBasicMaterial({ color: '#c8472d', side: THREE.DoubleSide }) : new THREE.MeshBasicMaterial({ color: '#c8472d', wireframe: true, side: THREE.DoubleSide })
    material.depthTest = false
    const window = new THREE.Mesh(geometry, material); window.position.fromArray(d.centre); window.renderOrder = 11
    if (d.verticalFacade) window.rotation.y = Math.PI / 2
    group.add(window)
  }
  scene.add(group)
  return d
}

function addSunpath(scene, result, target) {
  if (!result?.sunpath) return
  const centre = new THREE.Vector3(...target)
  result.sunpath.forEach((path, index) => {
    const points = path.samples.map(sample => {
      const altitude = THREE.MathUtils.degToRad(sample.altitude), azimuth = THREE.MathUtils.degToRad(sample.azimuth)
      const radius = 115
      return new THREE.Vector3(centre.x + Math.sin(azimuth) * Math.cos(altitude) * radius, centre.y + Math.sin(altitude) * radius, centre.z - Math.cos(azimuth) * Math.cos(altitude) * radius)
    })
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: seasonal[index], linewidth: 2 })); line.userData.kind = 'overlay'; scene.add(line)
  })
}

function addShadows(scene, context, result, time) {
  const sample = result?.shadow?.samples.find(item => item.time === time)
  if (!sample) return
  const altitude = THREE.MathUtils.degToRad(Math.max(2, sample.altitude)), azimuth = THREE.MathUtils.degToRad(sample.azimuth)
  const dx = -Math.sin(azimuth) / Math.tan(altitude), dz = Math.cos(azimuth) / Math.tan(altitude)
  for (const building of context.buildings) {
    const material = new THREE.MeshBasicMaterial({ color: '#45534d', transparent: true, opacity: .22, side: THREE.DoubleSide, depthWrite: false })
    const base = building.footprint.map(([x, y]) => new THREE.Vector3(x, .04, -y))
    const projected = building.footprint.map(([x, y]) => new THREE.Vector3(x + dx * building.height_m, .04, -y + dz * building.height_m))
    const group = new THREE.Group(); group.userData.kind = 'overlay'
    const roof = new THREE.Shape(projected.map(point => new THREE.Vector2(point.x, point.z)))
    const roofMesh = new THREE.Mesh(new THREE.ShapeGeometry(roof), material); roofMesh.rotation.x = Math.PI / 2; group.add(roofMesh)
    for (let index = 0; index < base.length; index++) {
      const next = (index + 1) % base.length
      const geometry = new THREE.BufferGeometry().setFromPoints([base[index], base[next], projected[next], base[index], projected[next], projected[index]])
      group.add(new THREE.Mesh(geometry, material))
    }
    scene.add(group)
  }
}

export function disposeObject(root) {
  root.traverse?.(object => {
    object.geometry?.dispose?.()
    const materials = Array.isArray(object.material) ? object.material : object.material ? [object.material] : []
    materials.forEach(material => { for (const value of Object.values(material)) if (value?.isTexture) value.dispose(); material.dispose?.() })
  })
}

export function populateScene(scene, context, study, result, presentation) {
  while (scene.children.length) { const child = scene.children[0]; scene.remove(child); disposeObject(child) }
  scene.background = new THREE.Color('#d9ddd5')
  scene.add(new THREE.HemisphereLight('#fffdf2', '#5f665f', 2.2))
  const sun = new THREE.DirectionalLight('#fff3c4', 2.6); sun.position.set(-100, 120, -120); scene.add(sun)
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(720, 720), new THREE.MeshStandardMaterial({ color: '#f5f2e9', roughness: 1 })); ground.rotation.x = -Math.PI / 2; ground.userData.kind = 'ground'; scene.add(ground)
  const geometry = new THREE.Group(); geometry.userData.kind = 'geometry'; context?.buildings.forEach(building => geometry.add(buildingMesh(building, presentation))); scene.add(geometry)
  const home = addHome(scene, context, study, result, presentation)
  if (presentation.analysis === 'sunpath' && result) addSunpath(scene, result, home?.centre || [0, 50, 0])
  if (presentation.analysis === 'shadow' && result) addShadows(scene, context, result, presentation.shadowTime)
  return { geometry, home }
}

export function boundsFor(group, home, preset) {
  if (preset === 'home' && home) {
    const [x, y, z] = home.centre; return new THREE.Box3(new THREE.Vector3(x - 4, y - 3, z - 4), new THREE.Vector3(x + 4, y + 3, z + 4))
  }
  if (preset === 'tower') {
    const tower = group.children.find(child => child.userData.kind === 'tower'); if (tower) return new THREE.Box3().setFromObject(tower)
  }
  return new THREE.Box3().setFromObject(group)
}

export function applyCameraPreset(camera, controls, bounds, preset, facade = 'east') {
  const frame = frameBounds({ min: bounds.min.toArray(), max: bounds.max.toArray() }, preset, facade)
  const size = bounds.getSize(new THREE.Vector3()), radius = size.length() / 2
  const vertical = THREE.MathUtils.degToRad(camera.fov), horizontal = 2 * Math.atan(Math.tan(vertical / 2) * camera.aspect)
  const fitDistance = radius / Math.sin(Math.max(.08, Math.min(vertical, horizontal) / 2)) * 1.08
  const target = new THREE.Vector3(...frame.target), direction = new THREE.Vector3(...frame.position).sub(target).normalize()
  camera.position.copy(target).addScaledVector(direction, Math.max(fitDistance, new THREE.Vector3(...frame.position).distanceTo(target)))
  camera.near = frame.near; camera.far = Math.max(frame.far, camera.position.distanceTo(target) * 8); camera.updateProjectionMatrix()
  controls.target.fromArray(frame.target); controls.update(); controls.saveState()
}

export function renderSiteEvidence(context, study, width = 1380, height = 1180) {
  const canvas = document.createElement('canvas'); let renderer; const scene = new THREE.Scene()
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: true })
    renderer.setPixelRatio(1); renderer.setSize(width, height, false)
    const camera = new THREE.PerspectiveCamera(38, width / height, .1, 3000)
    const { geometry, home } = populateScene(scene, context, study, null, { analysis: 'site_export', shadowTime: '12:00', solarDate: '2026-03-21' })
    const bounds = boundsFor(geometry, home, 'home'), frame = frameBounds({ min: bounds.min.toArray(), max: bounds.max.toArray() }, 'home', home?.facade)
    camera.position.fromArray(frame.position); camera.near = frame.near; camera.far = frame.far; camera.lookAt(...frame.target); camera.updateProjectionMatrix(); renderer.render(scene, camera)
    return canvas
  } finally { disposeObject(scene); renderer?.dispose() }
}
