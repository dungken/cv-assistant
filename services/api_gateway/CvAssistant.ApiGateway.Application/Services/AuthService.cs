using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Security;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class AuthService : IAuthService
{
    private readonly IUserRepository _userRepository;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtUtils _jwtUtils;

    public AuthService(IUserRepository userRepository, IPasswordHasher passwordHasher, IJwtUtils jwtUtils)
    {
        _userRepository = userRepository;
        _passwordHasher = passwordHasher;
        _jwtUtils = jwtUtils;
    }

    public async Task<AuthResponse> RegisterAsync(RegisterRequest request)
    {
        if (await _userRepository.ExistsByEmailAsync(request.Email))
        {
            throw new Exception("Email already exists");
        }

        var user = new User
        {
            Name = request.Name,
            Email = request.Email,
            Password = _passwordHasher.Hash(request.Password),
            CreatedAt = DateTime.UtcNow
        };

        await _userRepository.AddAsync(user);

        var token = _jwtUtils.GenerateToken(user.Email);
        return new AuthResponse(token, user.Email, user.Name ?? string.Empty);
    }

    public async Task<AuthResponse> LoginAsync(LoginRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(request.Email) 
                   ?? throw new Exception("User not found");

        if (!_passwordHasher.Verify(request.Password, user.Password))
        {
            throw new Exception("Invalid credentials");
        }

        var token = _jwtUtils.GenerateToken(user.Email);
        return new AuthResponse(token, user.Email, user.Name ?? string.Empty);
    }
}
