import { describe, expect, it } from 'vitest'

import { initialState, reduce, toolActions } from './state'


describe('shared visible state', () => {
  it('produces identical state through UI and WebMCP actions', () => {
    const payload = { study_id: 'study-1', state: 'needs_confirmation' as const }
    expect(reduce(initialState, { type: 'study-created', payload, source: 'ui' }))
      .toEqual(reduce(initialState, { type: 'study-created', payload, source: 'webmcp' }))
  })

  it('does not expose confirmation as a tool action', () => {
    expect(toolActions).toEqual([
      'create_apartment_study',
      'propose_unit_location',
      'get_study_state',
      'run_solar_analysis',
      'show_analysis',
      'export_study',
    ])
    expect(toolActions).not.toContain('confirm_unit')
  })

  it('opens the first computed study when analysis completes', () => {
    const complete = reduce(
      { ...initialState, screen: 'analyse', status: 'analysing' },
      { type: 'study-state', payload: { state: 'complete' } },
    )
    expect(complete.analysis).toBe('sunpath')
  })

  it('uses one presentation action for UI and WebMCP selections', () => {
    const action = { type: 'show-analysis', analysis: 'shadow', shadowTime: '09:00', view: 'home' }
    const ui = reduce(initialState, { ...action, source: 'ui' })
    const webmcp = reduce(initialState, { ...action, source: 'webmcp' })
    expect(ui).toEqual(webmcp)
    expect(ui).toMatchObject({ analysis: 'shadow', shadowTime: '09:00', viewRequest: 'home' })
  })

  it('preserves a manually moved camera when only time or seasonal date changes', () => {
    const shadow = { ...initialState, screen: 'analyse' as const, analysis: 'shadow' as const, viewRevision: 4 }
    expect(reduce(shadow, { type: 'show-analysis', analysis: 'shadow', shadowTime: '15:00' }).viewRevision).toBe(4)
    const access = { ...shadow, analysis: 'solar_access' as const }
    expect(reduce(access, { type: 'show-analysis', analysis: 'solar_access', solarDate: '2026-12-21' }).viewRevision).toBe(4)
  })
})
