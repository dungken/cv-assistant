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
    private readonly IEmailService _emailService;

    public AuthService(IUserRepository userRepository, IPasswordHasher passwordHasher, IJwtUtils jwtUtils, IEmailService emailService)
    {
        _userRepository = userRepository;
        _passwordHasher = passwordHasher;
        _jwtUtils = jwtUtils;
        _emailService = emailService;
    }

    public async Task<AuthResponse> RegisterAsync(RegisterRequest request)
    {
        if (await _userRepository.ExistsByEmailAsync(request.Email))
        {
            throw new Exception("Email already exists");
        }

        var verificationToken = GenerateOtp();

        var user = new User
        {
            Name = request.Name,
            Email = request.Email,
            Password = _passwordHasher.Hash(request.Password),
            CreatedAt = DateTime.UtcNow,
            IsEmailVerified = false,
            EmailVerificationToken = verificationToken,
            EmailVerificationTokenExpiry = DateTime.UtcNow.AddHours(24)
        };

        var refreshToken = _jwtUtils.GenerateRefreshToken();
        user.RefreshToken = refreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(7);

        await _userRepository.AddAsync(user);

        await _emailService.SendEmailVerificationAsync(user.Email, verificationToken);

        var accessToken = _jwtUtils.GenerateAccessToken(user.Email, user.Role);
        return new AuthResponse(accessToken, refreshToken, user.Email, user.Name ?? string.Empty, user.Role);
    }

    public async Task<AuthResponse> LoginAsync(LoginRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(request.Email)
                   ?? throw new Exception("User not found");

        if (!_passwordHasher.Verify(request.Password, user.Password))
        {
            throw new Exception("Invalid credentials");
        }

        var accessToken = _jwtUtils.GenerateAccessToken(user.Email, user.Role);
        var refreshToken = _jwtUtils.GenerateRefreshToken();

        user.RefreshToken = refreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(7);
        await _userRepository.UpdateAsync(user);

        return new AuthResponse(accessToken, refreshToken, user.Email, user.Name ?? string.Empty, user.Role);
    }

    public async Task<AuthResponse> RefreshTokenAsync(RefreshTokenRequest request)
    {
        var user = await _userRepository.GetByRefreshTokenAsync(request.RefreshToken)
                   ?? throw new Exception("Invalid refresh token");

        if (user.RefreshTokenExpiryTime < DateTime.UtcNow)
        {
            throw new Exception("Refresh token expired");
        }

        var newAccessToken = _jwtUtils.GenerateAccessToken(user.Email, user.Role);
        var newRefreshToken = _jwtUtils.GenerateRefreshToken();

        user.RefreshToken = newRefreshToken;
        user.RefreshTokenExpiryTime = DateTime.UtcNow.AddDays(7);
        await _userRepository.UpdateAsync(user);

        return new AuthResponse(newAccessToken, newRefreshToken, user.Email, user.Name ?? string.Empty, user.Role);
    }

    public async Task VerifyEmailAsync(VerifyEmailRequest request)
    {
        var user = await _userRepository.GetByEmailVerificationTokenAsync(request.Token)
                   ?? throw new Exception("Invalid verification token");

        if (user.EmailVerificationTokenExpiry < DateTime.UtcNow)
        {
            throw new Exception("Verification token expired");
        }

        user.IsEmailVerified = true;
        user.EmailVerificationToken = null;
        user.EmailVerificationTokenExpiry = null;
        await _userRepository.UpdateAsync(user);
    }

    public async Task ForgotPasswordAsync(ForgotPasswordRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(request.Email);
        if (user == null) return; // Don't reveal if email exists

        var otp = GenerateOtp();
        user.PasswordResetToken = otp;
        user.PasswordResetTokenExpiry = DateTime.UtcNow.AddMinutes(15);
        await _userRepository.UpdateAsync(user);

        await _emailService.SendPasswordResetAsync(user.Email, otp);
    }

    public async Task ResetPasswordAsync(ResetPasswordRequest request)
    {
        var user = await _userRepository.GetByPasswordResetTokenAsync(request.Email, request.Otp)
                   ?? throw new Exception("Invalid OTP");

        if (user.PasswordResetTokenExpiry < DateTime.UtcNow)
        {
            throw new Exception("OTP expired");
        }

        user.Password = _passwordHasher.Hash(request.NewPassword);
        user.PasswordResetToken = null;
        user.PasswordResetTokenExpiry = null;
        await _userRepository.UpdateAsync(user);
    }

    private static string GenerateOtp()
    {
        return Random.Shared.Next(100000, 999999).ToString();
    }
}
