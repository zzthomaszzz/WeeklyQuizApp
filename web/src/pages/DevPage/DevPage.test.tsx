import { render, screen } from '@testing-library/react'
import { DevPage } from './DevPage'

describe('DevPage', () => {
    it('renders a submit button', () => {
        render(<DevPage />)
        const button = screen.getByRole('button', { name: /submit/i })
        expect(button).toBeInTheDocument();
    })

    it('renders a name text box', () => {
        render(<DevPage />)
        const name = screen.getByRole('textbox', { name: /name/i })
        expect(name).toBeInTheDocument();
    })

    it('renders a password text box', () => {
        render(<DevPage />)
        const password = screen.getByLabelText(/password/i)
        expect(password).toBeInTheDocument();
        expect(password).toHaveAttribute('type', 'password')
    })
})