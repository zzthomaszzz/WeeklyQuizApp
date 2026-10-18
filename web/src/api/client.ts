export interface User {
  id: number
  email: string
  name: string
  role: 'student' | 'lecturer'
}
export interface DashboardData {
  user: User
  courses: { id: number; code: string; name: string }[]
  quizzes: { id: number; course_id: number; week_number: number; title: string; opens_at: string | null; closes_at: string | null }[]
}

/* ---- taking a quiz ------------------------------------------------------ */

/** An answer choice as a student sees it. Correctness is deliberately absent:
 *  the server never sends it before the attempt is submitted. */
export interface QuizOption {
  id: number
  question_id: number
  text: string
  position: number
}
export interface QuizQuestion {
  id: number
  quiz_id: number
  text: string
  topic_tag: string | null
  position: number
  options: QuizOption[]
}
export interface GradedAnswer {
  question_id: number
  selected_option_id: number
  is_correct: boolean
}
export interface AttemptResult {
  attempt_id: number
  score: number
  max_score: number
  answers: GradedAnswer[]
}

/* ---- authoring a quiz --------------------------------------------------- */

export interface CreatedQuiz {
  id: number
  course_id: number
  week_number: number
  title: string
  status: string
  max_attempts: number | null
}
/** The lecturer authored these answers, so correctness is theirs to see.
 *  QuizOption above is the shape a student gets. */
export interface CreatedOption {
  id: number
  text: string
  is_correct: boolean
  position: number
}
export interface CreatedQuestion {
  id: number
  quiz_id: number
  text: string
  topic_tag: string | null
  position: number
  options: CreatedOption[]
}

/* ---- transport ---------------------------------------------------------- */

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch('/api' + path, { ...options, credentials: 'same-origin' })
  } catch {
    throw new Error('Cannot reach the server. Please try again.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, typeof body?.detail === 'string' ? body.detail : 'Unable to load data. Please try again.')
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function patchJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

/** Clears the session cookie. The server owns the cookie, so there is
 *  nothing to remove on this side. */
export function logout(): Promise<void> {
  return request<void>('/auth/logout', { method: 'POST' })
}
