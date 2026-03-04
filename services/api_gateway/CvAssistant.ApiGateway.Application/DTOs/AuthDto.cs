namespace CvAssistant.ApiGateway.Application.DTOs;

public record RegisterRequest(string Email, string Password, string Name);
public record LoginRequest(string Email, string Password);
public record AuthResponse(string Token, string Email, string Name);
