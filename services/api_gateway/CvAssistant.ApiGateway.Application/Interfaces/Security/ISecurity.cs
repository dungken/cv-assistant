namespace CvAssistant.ApiGateway.Application.Interfaces.Security;

public interface IJwtUtils
{
    string GenerateAccessToken(string email, string role);
    string GenerateRefreshToken();
    string? GetEmailFromToken(string token);
}

public interface IPasswordHasher
{
    string Hash(string password);
    bool Verify(string password, string hashedPassword);
}

public interface IEmailService
{
    Task SendEmailVerificationAsync(string toEmail, string token);
    Task SendPasswordResetAsync(string toEmail, string otp);
}
