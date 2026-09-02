import { describe, expect, it } from 'vitest'

import { conciseStudyState, DEFAULT_PROPOSAL, validateShowAnalysis } from './webmcp'

describe('show_analysis validation', () => {
  it('accepts supported presentation controls', () => {
    expect(validateShowAnalysis({ analysis: 'shadow', shadow_time: '15:00', view: 'tower' }))
      .toEqual({ analysis: 'shadow', shadowTime: '15:00', view: 'tower' })
    expect(validateShowAnalysis({ analysis: 'solar_access', solar_date: '2026-12-21', view: 'home' }))
      .toEqual({ analysis: 'solar_access', solarDate: '2026-12-21', view: 'home' })
  })

  it('rejects malformed direct calls without creating undefined state', () => {
    expect(() => validateShowAnalysis({ analysis: undefined })).toThrowError('INVALID_PRESENTATION')
    expect(() => validateShowAnalysis({ analysis: 'shadow', shadow_time: '10:00' })).toThrowError('INVALID_PRESENTATION')
    expect(() => validateShowAnalysis({ analysis: 'radiation', solar_date: '2026-03-21' })).toThrowError('INVALID_PRESENTATION')
    expect(() => validateShowAnalysis({ analysis: 'shadow', shadow_time: '' })).toThrowError('INVALID_PRESENTATION')
    expect(() => validateShowAnalysis({ analysis: 'shadow', surprise: true })).toThrowError('INVALID_PRESENTATION')
  })
})

describe('study state privacy boundary', () => {
  it('keeps the agent proposal deterministic while leaving confirmation to the resident', () => {
    expect(DEFAULT_PROPOSAL).toMatchObject({ mirrored: false, window_width: 4, window_height: 1.2, sill_height: .9 })
    expect(DEFAULT_PROPOSAL).not.toHaveProperty('width')
    expect(DEFAULT_PROPOSAL).not.toHaveProperty('depth')
    expect(DEFAULT_PROPOSAL).not.toHaveProperty('confirmed')
  })

  it('keeps complete plate geometry out of WebMCP results', () => {
    const state = conciseStudyState({
      study_id: 'study-1', state: 'needs_confirmation', next_action: 'Confirm.',
      plate: { outline_xyz: [[1, 2, 3]], sensor_xyz: [[1, 2, 3]] },
      plate_summary: { usable_area_m2: 32, sensor_count: 128, spacing_m: .5, normal_state: 'sourced_edge' },
    })
    expect(state).toMatchObject({ study_id: 'study-1', plate_summary: { usable_area_m2: 32 } })
    expect(state).not.toHaveProperty('plate')
  })
})
