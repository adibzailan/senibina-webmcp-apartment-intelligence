// @ts-expect-error Vitest provides Node's built-in module; the production bundle does not import this test.
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const css = readFileSync(new URL('./style.css', import.meta.url), 'utf8')
const app = readFileSync(new URL('./App.jsx', import.meta.url), 'utf8')
const scene = readFileSync(new URL('./Scene.jsx', import.meta.url), 'utf8')

describe('Apartment Intelligence design contract', () => {
  it('self-hosts both approved font roles and defines the responsive grids', () => {
    expect(css).toContain("font-family:Newsreader")
    expect(css).toContain("font-family:Inter")
    expect(css).toContain('repeat(12,1fr)')
    expect(css).toContain('repeat(6,1fr)')
    expect(css).toContain('repeat(4,1fr)')
  })

  it('keeps all interactive controls at or above the 44px design target', () => {
    expect(css).toContain('min-height:44px')
    expect(css).toContain('button:focus-visible')
    expect(css).toContain('@media(prefers-reduced-motion:reduce)')
  })

  it('provides a real architectural camera and all analysis legends', () => {
    expect(scene).toContain('OrbitControls')
    for (const control of ['Precinct', 'Block 87', 'Home', 'Reset view']) expect(scene).toContain(control)
    for (const analysis of ["analysis === 'sunpath'", "analysis === 'shadow'", "analysis === 'solar_access'", "analysis === 'radiation'"]) expect(scene).toContain(analysis)
  })

  it('uses one editorial workbench instead of the rejected title and tab strip', () => {
    expect(app).toContain('className="workbench"')
    expect(readFileSync(new URL('./DesignPrimitives.jsx', import.meta.url), 'utf8')).toContain('How does the sun meet this home?')
    expect(app).not.toContain('<h1>Apartment<br/>')
    expect(app).not.toContain('SENIBINA / CONSUMER ENVIRONMENTAL STUDY')
  })

  it('does not repeat the four analyses below the interactive workbench', () => {
    expect(app).not.toContain('evidence-chapters')
    expect(app).not.toContain('Four readings of the same home.')
    expect(css).not.toContain('.evidence-chapters')
  })

  it('starts without filler status copy or a divider above status messages', () => {
    expect(app).not.toContain('Ready for one reproducible Dawson study.')
    expect(app).toContain('{message && <p className="status" role="status">{message}</p>}')
    expect(css).not.toMatch(/\.status\{[^}]*border-top/)
    expect(css).toMatch(/\.workbench\{[^}]*border-bottom/)
  })
})
