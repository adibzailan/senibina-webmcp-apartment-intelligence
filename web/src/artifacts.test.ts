import { describe, expect, it } from 'vitest'

import { CARD_HEIGHT, CARD_NAMES, CARD_WIDTH, cardNarrative, exportManifest } from './artifacts'


describe('architectural artifact contract', () => {
  it('uses five consistent 1600 by 2400 cards', () => {
    expect(CARD_NAMES).toHaveLength(5)
    expect([CARD_WIDTH, CARD_HEIGHT]).toEqual([1600, 2400])
    expect(exportManifest('digest')).toMatchObject({ digest: 'digest', cards: CARD_NAMES })
    expect(exportManifest('digest', { address: '88 Dawson Road', storey: 22 })).toMatchObject({ address: '88 Dawson Road', storey: 22 })
  })

  it('gives every card a distinct computed method and keeps radiation limitations visible', () => {
    const result = {
      shadow: { samples: [] }, solar_access: {},
      radiation: { average_kwh_m2: 100, limitations: ['no inter-reflection'] },
    } as any
    expect(new Set(CARD_NAMES.map(name => cardNarrative(name, result).method)).size).toBe(5)
    expect(cardNarrative('radiation', result).limitations).toContain('no inter-reflection')
    expect(cardNarrative('shadow', result).method).toContain('apartment floor plate')
    expect(cardNarrative('solar-access', result).limitations).not.toContain('16 × 8')
    expect(cardNarrative('radiation', result).method).toContain('confirmed window aperture')
  })
})
