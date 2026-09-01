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
})
