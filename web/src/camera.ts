export type ViewPreset = 'precinct' | 'tower' | 'home'
export type Vec3 = [number, number, number]

export const facadeDirection = (facade: string): Vec3 => ({
  east: [1, 0, 0], west: [-1, 0, 0], north: [0, 0, -1], south: [0, 0, 1],
}[facade] as Vec3)

export function presetForPresentation(screen: string, analysis: string): ViewPreset {
  if (screen === 'provide' || screen === 'verify') return 'precinct'
  if (screen === 'locate') return 'home'
  if (analysis === 'solar_access' || analysis === 'radiation') return 'home'
  return 'tower'
}

export function frameBounds(bounds: { min: Vec3, max: Vec3 }, preset: ViewPreset, facade = 'east') {
  const size: Vec3 = bounds.max.map((value, index) => Math.max(1, value - bounds.min[index])) as Vec3
  const target: Vec3 = bounds.min.map((value, index) => value + size[index] / 2) as Vec3
  const radius = Math.max(...size)
  const facadeVector = facadeDirection(facade)
  const direction: Vec3 = preset === 'home'
    ? [facadeVector[0] + (facadeVector[2] ? .32 : 0), .24, facadeVector[2] + (facadeVector[0] ? .32 : 0)]
    : preset === 'tower' ? [0, .55, 1] : [1, .8, 1]
  const distance = Math.max(preset === 'home' ? 36 : 0, radius * (preset === 'precinct' ? 1.45 : preset === 'tower' ? 1.35 : 2.2))
  const position: Vec3 = [
    target[0] + direction[0] * distance,
    Math.max(8, target[1] + Math.max(.32, direction[1]) * distance),
    target[2] + direction[2] * distance,
  ]
  return { position, target, near: Math.max(.1, distance / 500), far: Math.max(1000, distance * 8) }
}
