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
