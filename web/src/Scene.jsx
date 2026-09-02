import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { presetForPresentation } from './camera'
import { applyCameraPreset, boundsFor, disposeObject, populateScene } from './sceneRender'

export default function Scene({ context, study, result, analysis, screen, shadowTime, solarDate, viewRequest, viewRevision, onView }) {
  const host = useRef(null), compass = useRef(null), runtime = useRef(null), [ready, setReady] = useState(false)
  const render = () => runtime.current?.renderer.render(runtime.current.scene, runtime.current.camera)

  useEffect(() => {
    if (!host.current) return
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); host.current.replaceChildren(renderer.domElement)
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(38, 1, .1, 3000)
    const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = false; controls.screenSpacePanning = true; controls.minDistance = 3; controls.maxDistance = 900; controls.maxPolarAngle = Math.PI * .49
    controls.addEventListener('change', () => { renderer.render(scene, camera); if (compass.current) compass.current.style.transform = `rotate(${controls.getAzimuthalAngle()}rad)` })
    const resize = new ResizeObserver(entries => { const box = entries[0].contentRect; if (!box.width || !box.height) return; renderer.setSize(box.width, box.height, false); camera.aspect = box.width / box.height; camera.updateProjectionMatrix(); renderer.render(scene, camera) })
    resize.observe(host.current); runtime.current = { renderer, scene, camera, controls, preset: 'precinct', geometry: null, home: null }; setReady(true)
    return () => { resize.disconnect(); controls.dispose(); disposeObject(scene); renderer.dispose(); runtime.current = null }
  }, [])

  useEffect(() => {
    if (!runtime.current || !context) return
    const presentation = { analysis, screen, shadowTime, solarDate }
    const built = populateScene(runtime.current.scene, context, study, result, presentation)
    runtime.current.geometry = built.geometry; runtime.current.home = built.home; render()
    if (!runtime.current.hasFrame && built.geometry.children.length) { const preset = viewRequest || presetForPresentation(screen, analysis); runtime.current.preset = preset; applyCameraPreset(runtime.current.camera, runtime.current.controls, boundsFor(built.geometry, built.home, preset), preset, built.home?.facade); runtime.current.hasFrame = true; render() }
  }, [context, study, result, analysis, screen, shadowTime, solarDate])

  useEffect(() => {
    const value = runtime.current; if (!value?.geometry || value.geometry.children.length === 0) return
    const preset = viewRequest || presetForPresentation(screen, analysis); value.preset = preset
    applyCameraPreset(value.camera, value.controls, boundsFor(value.geometry, value.home, preset), preset, value.home?.facade); render()
  }, [screen, analysis, viewRequest, viewRevision, ready])

  const choose = preset => { const value = runtime.current; if (!value?.geometry) return; value.preset = preset; applyCameraPreset(value.camera, value.controls, boundsFor(value.geometry, value.home, preset), preset, value.home?.facade); render(); onView?.(preset) }
  const reset = () => { runtime.current?.controls.reset(); render() }
  return <div className="scene-shell">
    <div className="scene" ref={host} aria-label="Interactive three-dimensional Dawson precinct" data-canvas-ready={String(ready)} />
    <div className="camera-toolbar" aria-label="Camera views"><button onClick={() => choose('precinct')}>Precinct</button><button onClick={() => choose('tower')}>Block 87</button><button onClick={() => choose('home')} disabled={!study}>Home</button><button onClick={reset}>Reset view</button></div>
    <div className="north-indicator" aria-label="North direction">N<span ref={compass} aria-hidden="true">↑</span></div>
    <div className="scene-legend"><b>{analysis.replace('_', ' ')}</b>{analysis === 'sunpath' ? <><span className="legend-line solar">21 Mar / 21 Jun / 21 Sep / 21 Dec</span><span>N · E · S · W</span></> : analysis === 'shadow' ? <><span><i className="swatch sunlit"/>Sunlit floor</span><span><i className="swatch shaded"/>No direct sun</span></> : analysis === 'solar_access' && result ? <><span><i className="continuous-scale access"/>Floor direct-sun hours</span><span>0–{Math.max(...result.solar_access[solarDate].sensor_hours).toFixed(1)} h</span></> : analysis === 'radiation' && result ? <><span><i className="continuous-scale radiation"/>Interior floor exposure</span><span>{result.radiation.minimum_kwh_m2}–{result.radiation.maximum_kwh_m2} kWh/m²</span></> : <><span><i className="swatch context"/>Translucent massing</span><span><i className="swatch confirmed"/>Apartment floor plate</span></>}</div>
    <p className="view-help">Drag to orbit · right-drag to pan · wheel or pinch to zoom</p>
  </div>
}
