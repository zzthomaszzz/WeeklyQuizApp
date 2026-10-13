import type { DashboardData } from '../api/client'
export const dashboardFixture: DashboardData = {
  user: { id: 1, email: 'student@example.test', name: 'Test Student', role: 'student' },
  courses: [{ id: 1, code: 'ENSE707', name: 'Course 1' }, { id: 2, code: 'COMP603', name: 'Course 2' }],
  quizzes: [
    { id: 1, course_id: 1, week_number: 1, title: 'Example 1', opens_at: null, closes_at: null },
    { id: 2, course_id: 2, week_number: 2, title: 'Example 2', opens_at: null, closes_at: null },
    { id: 3, course_id: 1, week_number: 3, title: 'Example 3', opens_at: null, closes_at: null },
  ],
}
