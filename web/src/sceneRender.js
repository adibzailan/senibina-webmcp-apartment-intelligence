import * as THREE from 'three'
import { frameBounds } from './camera'

const seasonal = ['#d6a928', '#d9772b', '#5b8f85', '#c8472d']

export function massingPresentation(screen) {
  const quiet = ['locate', 'analyse', 'export'].includes(screen)
  return { transparent: quiet, opacity: quiet ? .16 : 1, depthWrite: !quiet }
}

function buildingMesh(building, presentation, targetAddress) {
  const shape = new THREE.Shape(building.footprint.map(([x, y]) => new THREE.Vector2(x, -y)))
  const geometry = new THREE.ExtrudeGeometry(shape, { depth: building.height_m, bevelEnabled: false })
  geometry.rotateX(-Math.PI / 2)
  const materialState = massingPresentation(presentation.screen)
  const isTarget = building.address === targetAddress
  const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: isTarget ? '#d8d3c7' : '#fbfaf6', roughness: .9,
    ...materialState }))
  mesh.userData.kind = isTarget ? 'tower' : 'context'
  if (isTarget) {
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 24), new THREE.LineBasicMaterial({ color: '#5f665f', transparent: true, opacity: .55 }))
    mesh.add(edges)
  }
  return mesh
}

export function plateDescriptor(source) {
  const plate = source?.plate
  if (!plate) return null
  const outline = plate.outline_xyz.map(([x, y, z]) => [x, z, -y])
  const xs = outline.map(point => point[0]), ys = outline.map(point => point[1]), zs = outline.map(point => point[2])
  const columns = plate.grid[0], rows = plate.grid[1]
  const wallWidth = Math.hypot(plate.outline_xyz[1][0] - plate.outline_xyz[0][0], plate.outline_xyz[1][1] - plate.outline_xyz[0][1])
  const depth = Math.hypot(plate.outline_xyz[2][0] - plate.outline_xyz[1][0], plate.outline_xyz[2][1] - plate.outline_xyz[1][1])
  const cellWidth = wallWidth / columns, cellDepth = depth / rows
  const tangent = plate.wall_direction, inward = [-plate.normal[0], -plate.normal[1]]
  const cells = plate.sensor_xyz.map(([x, y, z], index) => {
    const corner = (u, v) => [x + tangent[0] * u + inward[0] * v, y + tangent[1] * u + inward[1] * v, z]
    return { position: [x, z, -y], size: [cellWidth, cellDepth], mask: plate.mask[index], index,
      outline_xyz: [corner(-cellWidth / 2, -cellDepth / 2), corner(cellWidth / 2, -cellDepth / 2), corner(cellWidth / 2, cellDepth / 2), corner(-cellWidth / 2, cellDepth / 2)] }
  })
  return {
    plate, outline, cells,
    centre: [(Math.min(...xs) + Math.max(...xs)) / 2, plate.elevation_m, (Math.min(...zs) + Math.max(...zs)) / 2],
    bounds: new THREE.Box3(new THREE.Vector3(Math.min(...xs), Math.min(...ys) - .05, Math.min(...zs)), new THREE.Vector3(Math.max(...xs), Math.max(...ys) + .05, Math.max(...zs))),
  }
}

export function homeDescriptor(context, study, result) {
  if (!context || !study) return null
  const target = context.buildings.find(building => building.address === study.address)
  if (!target) return null
  const descriptor = plateDescriptor(result || study)
  return descriptor ? { ...descriptor, target, facade: study.proposal.facade } : null
}

function addGrid(group, descriptor, values, colour) {
  const includedValues = values.filter((_, index) => descriptor.plate.mask[index])
  for (const cellDescriptor of descriptor.cells) {
    if (!cellDescriptor.mask) continue
    const value = values[cellDescriptor.index] ?? 0
    const shape = new THREE.Shape(cellDescriptor.outline_xyz.map(([x, y]) => new THREE.Vector2(x, -y)))
    const cell = new THREE.Mesh(new THREE.ShapeGeometry(shape), new THREE.MeshBasicMaterial({ color: colour(value, includedValues), side: THREE.DoubleSide, depthTest: false }))
    cell.geometry.rotateX(Math.PI / 2); cell.position.y = descriptor.plate.elevation_m + .035; cell.renderOrder = 12; group.add(cell)
  }
}

function addHome(scene, context, study, result, presentation) {
  const d = homeDescriptor(context, study, result)
  if (!d) return null
  const group = new THREE.Group(); group.userData.kind = 'home'
  const confirmed = study.state === 'ready' || study.state === 'complete' || Boolean(study.confirmation)
  if (confirmed) {
    addGrid(group, d, d.plate.mask, () => '#c8472d')
  } else {
    const plateShape = new THREE.Shape(d.plate.outline_xy.slice(0, -1).map(([x, y]) => new THREE.Vector2(x, -y)))
    const zone = new THREE.Mesh(new THREE.ShapeGeometry(plateShape), new THREE.MeshBasicMaterial({ color: '#c8472d', transparent: true, opacity: .12, wireframe: true, side: THREE.DoubleSide, depthTest: false }))
    zone.geometry.rotateX(Math.PI / 2); zone.position.y = d.plate.elevation_m; zone.renderOrder = 10; group.add(zone)
  }
  if (result && presentation.analysis === 'radiation') {
    const values = result.radiation.sensor_values_kwh_m2, min = result.radiation.minimum_kwh_m2, max = result.radiation.maximum_kwh_m2
    addGrid(group, d, values, value => new THREE.Color().setHSL((205 - ((value - min) / Math.max(1, max - min)) * 193) / 360, .62, .48))
  } else if (result && presentation.analysis === 'solar_access') {
    const values = result.solar_access[presentation.solarDate]?.sensor_hours || []
    const max = Math.max(1, ...values)
    addGrid(group, d, values, value => new THREE.Color().lerpColors(new THREE.Color('#183f5a'), new THREE.Color('#f2c230'), value / max))
  } else if (result && presentation.analysis === 'shadow') {
    const values = result.shadow.samples.find(sample => sample.time === presentation.shadowTime)?.sensor_values || []
    addGrid(group, d, values, value => value ? '#f2c230' : '#45534d')
  }
  const aperture = d.plate.aperture
  const geometry = new THREE.PlaneGeometry(aperture.width_m, aperture.height_m)
  const material = new THREE.MeshBasicMaterial({ color: '#c8472d', wireframe: !confirmed, side: THREE.DoubleSide, depthTest: false })
  const window = new THREE.Mesh(geometry, material); window.position.set(aperture.centre_xyz[0], aperture.centre_xyz[2], -aperture.centre_xyz[1]); window.renderOrder = 11
  window.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(d.plate.normal[0], 0, -d.plate.normal[1]).normalize()); group.add(window)
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
  const geometry = new THREE.Group(); geometry.userData.kind = 'geometry'; context?.buildings.forEach(building => geometry.add(buildingMesh(building, presentation, study?.address))); scene.add(geometry)
  const home = addHome(scene, context, study, result, presentation)
  if (presentation.analysis === 'sunpath' && result) addSunpath(scene, result, home?.centre || [0, 50, 0])
  return { geometry, home }
}

export function boundsFor(group, home, preset) {
  if (preset === 'home' && home) {
    return home.bounds.clone().expandByScalar(1)
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
    const { geometry, home } = populateScene(scene, context, study, null, { analysis: 'site_export', screen: 'export', shadowTime: '12:00', solarDate: '2026-03-21' })
    const bounds = boundsFor(geometry, home, 'home'), frame = frameBounds({ min: bounds.min.toArray(), max: bounds.max.toArray() }, 'home', home?.facade)
    camera.position.fromArray(frame.position); camera.near = frame.near; camera.far = frame.far; camera.lookAt(...frame.target); camera.updateProjectionMatrix(); renderer.render(scene, camera)
    return canvas
  } finally { disposeObject(scene); renderer?.dispose() }
}
