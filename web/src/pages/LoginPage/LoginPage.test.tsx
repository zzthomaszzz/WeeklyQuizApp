import { MemoryRouter } from 'react-router'
import { render, screen } from '@testing-library/react'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
    it('renders a submit button', () => {
        render(<MemoryRouter><LoginPage /></MemoryRouter>)
        const button = screen.getByRole('button', { name: /submit/i })
        expect(button).toBeInTheDocument();
    })

    it('renders a email text box', () => {
        render(<MemoryRouter><LoginPage /></MemoryRouter>)
        const name = screen.getByRole('textbox', { name: /email/i })
        expect(name).toBeInTheDocument();
    })

    it('renders a password text box', () => {
        render(<MemoryRouter><LoginPage /></MemoryRouter>)
        const password = screen.getByLabelText(/password/i)
        expect(password).toBeInTheDocument();
        expect(password).toHaveAttribute('type', 'password')
    })
})
