export const toolActions = [
  'create_apartment_study',
  'propose_unit_location',
  'get_study_state',
  'run_solar_analysis',
  'show_analysis',
  'export_study',
] as const

export type StudyStatus = 'draft' | 'needs_confirmation' | 'ready' | 'analysing' | 'complete'
export type Screen = 'provide' | 'verify' | 'locate' | 'analyse' | 'export'
export type State = {
  screen: Screen
  studyId?: string
  status: StudyStatus
  analysis: 'site' | 'sunpath' | 'shadow' | 'solar_access' | 'radiation'
  revision?: number
  shadowTime: '09:00' | '12:00' | '15:00'
  solarDate: '2026-03-21' | '2026-06-21' | '2026-09-21' | '2026-12-21'
  viewRequest?: 'precinct' | 'tower' | 'home'
  viewRevision: number
  lastSource?: 'ui' | 'webmcp'
}

export const initialState: State = { screen: 'provide', status: 'draft', analysis: 'site', shadowTime: '12:00', solarDate: '2026-03-21', viewRevision: 0 }

export function reduce(state: State, action: any): State {
  switch (action.type) {
    case 'study-created':
      return { ...state, studyId: action.payload.study_id, status: action.payload.state, screen: 'verify' }
    case 'show-screen':
      return { ...state, screen: action.screen, viewRequest: undefined, viewRevision: state.viewRevision + Number(action.screen !== state.screen) }
    case 'study-state':
      return { ...state, status: action.payload.state, revision: action.payload.proposal_revision ?? state.revision,
        screen: action.payload.state === 'complete' ? 'analyse' : state.screen,
        analysis: action.payload.state === 'complete' && state.analysis === 'site' ? 'sunpath' : state.analysis }
    case 'show-analysis':
      return { ...state, analysis: action.analysis, screen: 'analyse',
        shadowTime: action.shadowTime ?? state.shadowTime,
        solarDate: action.solarDate ?? state.solarDate,
        viewRequest: action.view,
        viewRevision: state.viewRevision + Number(action.analysis !== state.analysis || Boolean(action.view)) }
    case 'show-view':
      return { ...state, viewRequest: action.view, viewRevision: state.viewRevision + 1 }
    default:
      return state
  }
}
