// Database names supplied by the project team. Confirm ID types, nullability,
// and allowed role/status values against the API before connecting live data.
type Id = number
type Timestamp = string

export interface User {
  id: Id
  email: string
  name: string
  role: string
}
// password_hash belongs to the users table, but must never reach the browser.
export interface Course {
  id: Id
  code: string
  name: string
  lecturer_id: Id
  enrol_code: string
}
export interface Enrolment {
  id: Id
  student_id: Id
  course_id: Id
  enrolled_at: Timestamp
}
export interface Quiz {
  id: Id
  course_id: Id
  week_number: number
  title: string
  status: string
  opens_at: Timestamp | null
  closes_at: Timestamp | null
}
export interface Question {
  id: Id
  quiz_id: Id
  text: string
  position: number
}
export interface StudentOption {
  id: Id
  question_id: Id
  text: string
  position: number
}
// Only lecturer endpoints or post-submission feedback may return correctness.
export interface LecturerOption extends StudentOption {
  is_correct: boolean
}
export interface Attempt {
  id: Id
  quiz_id: Id
  student_id: Id
  submitted_at: Timestamp | null
  score: number | null
  max_score: number
}
export interface Answer {
  id: Id
  attempt_id: Id
  question_id: Id
  selected_option_id: Id
}
