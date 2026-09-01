import { useEffect, useRef } from 'react'
import * as THREE from 'three'


export default function Scene({ context, study, result, analysis, selected = '87' }) {
  const host = useRef(null)
  const canvas = useRef(null)
  useEffect(() => {
    if (!host.current || !context) return
    const width = host.current.clientWidth, height = host.current.clientHeight
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(width, height); canvas.current = renderer.domElement
    host.current.replaceChildren(renderer.domElement)
    const scene = new THREE.Scene(); scene.background = new THREE.Color('#dbe4db')
    const camera = new THREE.PerspectiveCamera(38, width / height, 1, 1200); camera.position.set(230, -260, 210)
    camera.lookAt(0, 0, 55)
    scene.add(new THREE.HemisphereLight('#fff9df', '#5a665d', 2.5))
    const sun = new THREE.DirectionalLight('#fff0bd', 3); sun.position.set(-80, -100, 240); scene.add(sun)
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(700, 700), new THREE.MeshStandardMaterial({ color: '#eae7dd' }))
    ground.rotation.x = -Math.PI / 2; scene.add(ground)
    for (const building of context.buildings) {
      const shape = new THREE.Shape(building.footprint.map(([x, y]) => new THREE.Vector2(x, -y)))
      const geometry = new THREE.ExtrudeGeometry(shape, { depth: building.height_m, bevelEnabled: false })
      geometry.rotateX(-Math.PI / 2)
      const material = new THREE.MeshStandardMaterial({ color: building.block === selected ? '#d95c37' : '#eee8dc', roughness: .85 })
      scene.add(new THREE.Mesh(geometry, material))
    }
    if (study) {
      const target = context.buildings.find(building => building.address === study.address)
      if (target) {
        const xs = target.footprint.map(point => point[0]), ys = target.footprint.map(point => point[1])
        const facade = study.proposal.facade, horizontal = facade === 'east' || facade === 'west'
        const factor = { left: .25, centre: .5, right: .75 }[study.proposal.position]
        const span = horizontal ? [Math.min(...ys), Math.max(...ys)] : [Math.min(...xs), Math.max(...xs)]
        const centre = span[0] + (span[1] - span[0]) * factor
        const fixed = facade === 'east' ? Math.max(...xs) + .08 : facade === 'west' ? Math.min(...xs) - .08 : facade === 'north' ? Math.max(...ys) + .08 : Math.min(...ys) - .08
        const base = (study.storey - 1) * 3 + study.proposal.sill_height
        const group = new THREE.Group()
        if (analysis === 'radiation' && result) {
          const values = result.radiation.sensor_values_kwh_m2, min = result.radiation.minimum_kwh_m2, max = result.radiation.maximum_kwh_m2
          for (let row = 0; row < 8; row++) for (let col = 0; col < 16; col++) {
            const ratio = max === min ? .5 : (values[row * 16 + col] - min) / (max - min)
            const cell = new THREE.Mesh(new THREE.PlaneGeometry(study.proposal.window_width / 16 * .94, study.proposal.window_height / 8 * .9), new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL((45 - ratio * 33) / 360, .78, .55), side: THREE.DoubleSide }))
            const along = centre - study.proposal.window_width / 2 + study.proposal.window_width * (col + .5) / 16
            cell.position.set(horizontal ? fixed : along, base + study.proposal.window_height * (row + .5) / 8, horizontal ? along : -fixed)
            if (horizontal) cell.rotation.y = Math.PI / 2
            group.add(cell)
          }
        } else {
          const window = new THREE.Mesh(new THREE.PlaneGeometry(study.proposal.window_width, study.proposal.window_height), new THREE.MeshBasicMaterial({ color: '#17231e', side: THREE.DoubleSide }))
          window.position.set(horizontal ? fixed : centre, base + study.proposal.window_height / 2, horizontal ? centre : -fixed)
          if (horizontal) window.rotation.y = Math.PI / 2
          group.add(window)
        }
        scene.add(group)
      }
    }
    renderer.render(scene, camera)
    return () => renderer.dispose()
  }, [context, selected, study, result, analysis])
  return <div className="scene" ref={host} aria-label="Three-dimensional Dawson precinct massing" data-canvas-ready={Boolean(canvas.current)} />
}
