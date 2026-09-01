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
  lastSource?: 'ui' | 'webmcp'
}

export const initialState: State = { screen: 'provide', status: 'draft', analysis: 'site' }

export function reduce(state: State, action: any): State {
  switch (action.type) {
    case 'study-created':
      return { ...state, studyId: action.payload.study_id, status: action.payload.state, screen: 'verify' }
    case 'show-screen':
      return { ...state, screen: action.screen }
    case 'study-state':
      return { ...state, status: action.payload.state, revision: action.payload.proposal_revision ?? state.revision,
        screen: action.payload.state === 'complete' ? 'analyse' : state.screen,
        analysis: action.payload.state === 'complete' && state.analysis === 'site' ? 'sunpath' : state.analysis }
    case 'show-analysis':
      return { ...state, analysis: action.analysis, screen: 'analyse' }
    default:
      return state
  }
}
