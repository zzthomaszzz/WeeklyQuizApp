import { dashboardFixture } from '../../test/dashboardFixture'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Dashboard } from './Dashboard'

describe('Student dashboard', () => {
  it('filters quizzes by search and course', async () => {
    const user = userEvent.setup()
    render(<Dashboard data={dashboardFixture} />)
    await user.type(screen.getByRole('searchbox'), 'Example 1')
    expect(screen.getByRole('heading', { name: 'Example 1' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Example 3' })).not.toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Course'), '2')
    expect(screen.getByText('No quizzes found')).toBeInTheDocument()
  })

})


