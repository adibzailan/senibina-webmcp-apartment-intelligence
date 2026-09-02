import { describe, expect, it } from 'vitest'

import { facadeDirection, presetForPresentation, frameBounds } from './camera'

describe('architectural camera', () => {
  it('maps geographic facades into the Three.js east north up frame', () => {
    expect(facadeDirection('east')).toEqual([1, 0, 0])
    expect(facadeDirection('west')).toEqual([-1, 0, 0])
    expect(facadeDirection('north')).toEqual([0, 0, -1])
    expect(facadeDirection('south')).toEqual([0, 0, 1])
  })

  it('places every home camera outside its requested facade', () => {
    for (const facade of ['north', 'east', 'south', 'west']) {
      const frame = frameBounds({ min: [-4, 80, -4], max: [4, 86, 4] }, 'home', facade)
      const direction = facadeDirection(facade)
      const delta = frame.position.map((value, index) => value - frame.target[index])
      expect(delta[0] * direction[0] + delta[2] * direction[2]).toBeGreaterThan(0)
    }
  })

  it('selects stage-aware presets', () => {
    expect(presetForPresentation('provide', 'site')).toBe('precinct')
    expect(presetForPresentation('locate', 'site')).toBe('home')
    expect(presetForPresentation('analyse', 'sunpath')).toBe('precinct')
    expect(presetForPresentation('analyse', 'shadow')).toBe('home')
    expect(presetForPresentation('analyse', 'radiation')).toBe('home')
  })

  it('frames finite geometry above ground', () => {
    const frame = frameBounds({ min: [-20, 0, -10], max: [40, 141, 30] }, 'precinct')
    expect(frame.position.every(Number.isFinite)).toBe(true)
    expect(frame.target.every(Number.isFinite)).toBe(true)
    expect(frame.position[1]).toBeGreaterThan(0)
    expect(frame.near).toBeGreaterThan(0)
    expect(frame.far).toBeGreaterThan(frame.near)
  })

  it('keeps facade evidence far enough from the camera to read as a drawing', () => {
    const frame = frameBounds({ min: [-4, 87, -4], max: [4, 93, 4] }, 'home', 'east')
    expect(frame.position[0] - frame.target[0]).toBeGreaterThanOrEqual(2.5)
    expect(frame.position[1] - frame.target[1]).toBeGreaterThanOrEqual(35)
  })
})
