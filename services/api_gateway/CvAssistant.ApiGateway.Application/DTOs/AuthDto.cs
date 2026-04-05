namespace CvAssistant.ApiGateway.Application.DTOs;

public record RegisterRequest(string Email, string Password, string Name);
public record LoginRequest(string Email, string Password);
public record AuthResponse(string Token, string RefreshToken, string Email, string Name, string Role);
public record RefreshTokenRequest(string RefreshToken);
public record VerifyEmailRequest(string Token);
public record ForgotPasswordRequest(string Email);
public record ResetPasswordRequest(string Email, string Otp, string NewPassword);
