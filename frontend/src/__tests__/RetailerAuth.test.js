import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RetailerAuth from '../components/retailer/RetailerAuth';

// Create mocks
const mockNavigate = jest.fn();
const mockRequestPasswordReset = jest.fn();
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();
const mockCharitiesList = jest.fn();

// Mock modules
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }) => <div>{children}</div>,
  useNavigate: () => mockNavigate,
}));

jest.mock('../utils/api', () => ({
  auth: {
    requestPasswordReset: (...args) => mockRequestPasswordReset(...args),
    register: jest.fn(),
    login: jest.fn(),
  },
  charities: {
    list: (...args) => mockCharitiesList(...args),
  },
}));

jest.mock('sonner', () => ({
  toast: {
    success: (...args) => mockToastSuccess(...args),
    error: (...args) => mockToastError(...args),
  },
  Toaster: () => null,
}));

// Import after mocking
import * as api from '../utils/api';
import { toast } from 'sonner';

describe('RetailerAuth - Forgot Password Flow', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    mockNavigate.mockClear();
    mockRequestPasswordReset.mockClear();
    mockToastSuccess.mockClear();
    mockToastError.mockClear();
    mockCharitiesList.mockClear();
    
    // Set default mock implementations
    mockCharitiesList.mockResolvedValue({ data: [] });
    mockRequestPasswordReset.mockResolvedValue({ data: { status: 'success' } });
  });

  const renderComponent = () => {
    return render(<RetailerAuth />);
  };

  test('should open forgot password modal when "Forgot password?" link is clicked', async () => {
    renderComponent();

    // Find and click the "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    expect(forgotPasswordLink).toBeInTheDocument();

    fireEvent.click(forgotPasswordLink);

    // Assert that the modal opens
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Check for modal content
    expect(screen.getByText(/enter your email address and we'll send you a link to reset your password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
  });

  test('should pre-populate email when user has entered email in login form', async () => {
    renderComponent();

    // Enter email in the login form
    const emailInput = screen.getByTestId('retailer-login-email');
    await userEvent.type(emailInput, 'test@retailer.com');

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Assert that email is pre-filled in the modal
    await waitFor(() => {
      const modalEmailInput = screen.getByLabelText(/email address/i);
      expect(modalEmailInput).toHaveValue('test@retailer.com');
    });
  });

  test('should send password reset request and show success toast', async () => {
    // Mock successful API response
    mockRequestPasswordReset.mockResolvedValue({ data: { status: 'success' } });

    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Enter email address
    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'retailer@example.com');

    // Click "Send Reset Link" button
    const sendButton = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(sendButton);

    // Assert that API was called with correct data
    await waitFor(() => {
      expect(mockRequestPasswordReset).toHaveBeenCalledWith({
        email: 'retailer@example.com',
        role: 'DRLP',
      });
    });

    // Assert that success toast appears
    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith('Password reset instructions sent to retailer@example.com');
    });

    // Assert that modal closes after success
    await waitFor(() => {
      expect(screen.queryByText('Reset Password')).not.toBeInTheDocument();
    });
  });

  test('should show error toast when password reset request fails', async () => {
    // Mock API error
    const errorMessage = 'Failed to send reset email';
    mockRequestPasswordReset.mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Enter email address
    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'retailer@example.com');

    // Click "Send Reset Link" button
    const sendButton = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(sendButton);

    // Assert that error toast appears
    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(errorMessage);
    });

    // Modal should remain open on error
    expect(screen.getByText('Reset Password')).toBeInTheDocument();
  });

  test('should show error toast when email is empty', async () => {
    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Click "Send Reset Link" without entering email
    const sendButton = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(sendButton);

    // Assert that error toast appears
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please enter your email address');
    });

    // Assert that API was NOT called
    expect(api.auth.requestPasswordReset).not.toHaveBeenCalled();
  });

  test('should close modal when Cancel button is clicked', async () => {
    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Click Cancel button
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Assert that modal closes
    await waitFor(() => {
      expect(screen.queryByText('Reset Password')).not.toBeInTheDocument();
    });
  });

  test('should clear email input when modal closes after successful submission', async () => {
    // Mock successful API response
    api.auth.requestPasswordReset.mockResolvedValue({ data: { status: 'success' } });

    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Enter email and submit
    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'test@example.com');
    
    const sendButton = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(sendButton);

    // Wait for modal to close
    await waitFor(() => {
      expect(screen.queryByText('Reset Password')).not.toBeInTheDocument();
    });

    // Open modal again and check if email is cleared
    fireEvent.click(forgotPasswordLink);

    await waitFor(() => {
      const newEmailInput = screen.getByLabelText(/email address/i);
      expect(newEmailInput).toHaveValue('');
    });
  });

  test('should have correct role (DRLP) in password reset request', async () => {
    // Mock successful API response
    api.auth.requestPasswordReset.mockResolvedValue({ data: { status: 'success' } });

    renderComponent();

    // Click "Forgot password?" link
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password\?/i });
    fireEvent.click(forgotPasswordLink);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    // Enter email and submit
    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'retailer@dealshaq.com');
    
    const sendButton = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(sendButton);

    // Verify that the API was called with role: 'DRLP'
    await waitFor(() => {
      expect(api.auth.requestPasswordReset).toHaveBeenCalledWith({
        email: 'retailer@dealshaq.com',
        role: 'DRLP',
      });
    });
  });
});
