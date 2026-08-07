import {render, screen } from '@testing-library/react'
import { LoginPage } from './LoginPage'

describe('LoginPage', ()=> {
    it('renders a submit button', () => {
        render(<LoginPage/>)
        const button = screen.getByRole('button', {name: /submit/i})
        expect(button).toBeInTheDocument();
    })

    it('renders a name text box', () =>{
        render(<LoginPage/>)
        const name = screen.getByRole('textbox', {name: /name/i})
        expect(name).toBeInTheDocument();
    })

    it('renders a password text box', () =>{
        render(<LoginPage/>)
        const password = screen.getByLabelText(/password/i)
        expect(password).toBeInTheDocument();
        expect(password).toHaveAttribute('type', 'password')
    })
})