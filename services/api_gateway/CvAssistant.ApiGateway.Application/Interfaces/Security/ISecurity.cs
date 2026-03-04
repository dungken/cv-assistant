namespace CvAssistant.ApiGateway.Application.Interfaces.Security;

public interface IJwtUtils
{
    string GenerateToken(string email);
}

public interface IPasswordHasher
{
    string Hash(string password);
    bool Verify(string password, string hashedPassword);
}
