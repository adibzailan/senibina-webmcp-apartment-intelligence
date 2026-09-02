import { describe, expect, it } from 'vitest'

import { validateShowAnalysis } from './webmcp'

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
