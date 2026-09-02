import { describe, expect, it } from 'vitest'
import * as THREE from 'three'

import { massingPresentation, plateDescriptor, populateScene, sectionPlaneElevation } from './sceneRender'


const plate = {
  elevation_m: 87.02,
  outline_xy: [[20, 1], [20, 9], [17, 9], [17, 7], [14, 7], [14, 1], [20, 1]],
  outline_xyz: [[20, 1, 87.02], [20, 9, 87.02], [17, 9, 87.02], [17, 7, 87.02], [14, 7, 87.02], [14, 1, 87.02], [20, 1, 87.02]],
  anchor_xy: [20, 5], wall_direction: [0, 1], normal: [1, 0],
  grid: [4, 3], mask: Array(12).fill(1), sensor_xyz: Array.from({ length: 12 }, (_, index) => [19 - Math.floor(index / 4), 2 + index % 4 * 2, 87.02]),
  grid_origin_xyz: [20, 1, 87.02], grid_u_vector: [0, 2, 0], grid_v_vector: [-1, 0, 0],
  aperture: { centre_xyz: [20, 5, 88.5], width_m: 4, height_m: 1.2, sill_m: .9 },
}

describe('floor-plate scene contract', () => {
  it('maps the canonical east-north-up plate into a horizontal Three.js plane', () => {
    const descriptor = plateDescriptor({ plate } as any)!
    expect(descriptor.centre).toEqual([17, 87.02, -5])
    expect(descriptor.bounds.min.y).toBeCloseTo(86.97)
    expect(descriptor.bounds.max.y).toBeCloseTo(87.07)
    expect(descriptor.cells).toHaveLength(12)
    expect(new Set(descriptor.cells.map((cell: any) => cell.position[1]))).toEqual(new Set([87.02]))
    const firstCell = descriptor.cells[0].outline_xyz
    expect(firstCell[1][0] - firstCell[0][0]).toBeCloseTo(0)
    expect(firstCell[1][1] - firstCell[0][1]).toBeGreaterThan(0)
  })

  it('ghosts every building from Locate onward but not during initial research', () => {
    expect(massingPresentation('verify')).toEqual({ transparent: false, opacity: 1, depthWrite: true })
    expect(massingPresentation('locate')).toEqual({ transparent: true, opacity: .16, depthWrite: false })
    expect(massingPresentation('analyse')).toEqual({ transparent: true, opacity: .16, depthWrite: false })
  })

  it('cuts translucent massing just above the apartment floor', () => {
    expect(sectionPlaneElevation('locate', { plate: { elevation_m: 87 } })).toBeCloseTo(87.15)
    expect(sectionPlaneElevation('verify', { plate: { elevation_m: 87 } })).toBeNull()
  })

  it('shows shadow evidence on the apartment plate without a competing ground-shadow overlay', () => {
    const scene = new THREE.Scene()
    const context = { buildings: [{ block: '87', address: '87 Dawson Road', height_m: 120, footprint: [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]] }] }
    const study = { address: '87 Dawson Road', state: 'complete', proposal: { facade: 'east' }, plate }
    const result = { plate, shadow: { samples: [{ time: '12:00', altitude: 88, azimuth: 0, sensor_values: Array(12).fill(1) }] } }

    populateScene(scene, context, study, result, { screen: 'analyse', analysis: 'shadow', shadowTime: '12:00' })

    expect(scene.children.filter((child: any) => child.userData.kind === 'overlay')).toHaveLength(0)
  })
})
