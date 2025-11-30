import { Resend } from 'resend';

// Initialize Resend with your API key from .env
const resend = new Resend(process.env.RESEND_API_KEY);

// Function to send reset password email
export async function sendResetEmail(to, token) {
  await resend.emails.send({
    from: 'noreply@dealshaq.com', // or onboarding@resend.dev for testing
    to,
    subject: 'Reset your DealShaq password',
    html: `<p>Click <a href="https://dealshaq.com/reset-password?token=${token}">here</a> to reset your password.</p>`
  });
}
