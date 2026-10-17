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
export interface CreatedQuiz {
  id: number
  course_id: number
  week_number: number
  title: string
  status: string
  max_attempts: number | null
}
/** The lecturer authored these answers, so correctness is theirs to see.
 *  The student-facing shape omits it entirely. */
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
  return response.json()
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
