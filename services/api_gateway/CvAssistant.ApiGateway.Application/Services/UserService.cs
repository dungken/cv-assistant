using System.Text.Json;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Security;
using CvAssistant.ApiGateway.Application.Interfaces.Services;

namespace CvAssistant.ApiGateway.Application.Services;

public class UserService : IUserService
{
    private readonly IUserRepository _userRepository;
    private readonly ICVHistoryRepository _cvHistoryRepository;
    private readonly ICvDocumentRepository _cvDocumentRepository;
    private readonly IPasswordHasher _passwordHasher;

    private static readonly JsonSerializerOptions _jsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
    };

    public UserService(IUserRepository userRepository, ICVHistoryRepository cvHistoryRepository,
        ICvDocumentRepository cvDocumentRepository, IPasswordHasher passwordHasher)
    {
        _userRepository = userRepository;
        _cvHistoryRepository = cvHistoryRepository;
        _cvDocumentRepository = cvDocumentRepository;
        _passwordHasher = passwordHasher;
    }

    public async Task<UserProfileResponse> GetProfileAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var preferences = DeserializePreferences(user.PreferencesJson);
        var cvsCreated = await _cvDocumentRepository.CountByUserIdAsync(user.Id);
        var analysesDone = await _cvHistoryRepository.CountByUserIdAsync(user.Id);
        var stats = new UserStats(cvsCreated, analysesDone, 0);

        return new UserProfileResponse(
            user.Id, user.Email, user.Name ?? string.Empty, user.Bio ?? string.Empty,
            user.Phone, user.AvatarUrl, user.IsEmailVerified, preferences, stats, user.CreatedAt,
            user.Role ?? "User"
        );
    }

    public async Task<UserProfileResponse> UpdateProfileAsync(string email, UpdateUserRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        if (request.Name != null) user.Name = request.Name;
        if (request.Bio != null) user.Bio = request.Bio;
        if (request.Phone != null) user.Phone = request.Phone;
        if (request.Preferences != null) user.PreferencesJson = JsonSerializer.Serialize(request.Preferences, _jsonOptions);
        user.UpdatedAt = DateTime.UtcNow;

        await _userRepository.UpdateAsync(user);
        return await GetProfileAsync(email);
    }

    public async Task<UserProfileResponse> UploadAvatarAsync(string email, Stream fileStream, string fileName)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var uploadsDir = Path.Combine("wwwroot", "uploads", "avatars");
        Directory.CreateDirectory(uploadsDir);

        var ext = Path.GetExtension(fileName);
        var savedName = $"{user.Id}_{DateTime.UtcNow.Ticks}{ext}";
        var filePath = Path.Combine(uploadsDir, savedName);

        using (var fs = new FileStream(filePath, FileMode.Create))
        {
            await fileStream.CopyToAsync(fs);
        }

        user.AvatarUrl = $"/uploads/avatars/{savedName}";
        user.UpdatedAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user);

        return await GetProfileAsync(email);
    }

    public async Task ChangePasswordAsync(string email, ChangePasswordRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        if (!_passwordHasher.Verify(request.OldPassword, user.Password))
        {
            throw new Exception("Invalid credentials");
        }

        user.Password = _passwordHasher.Hash(request.NewPassword);
        user.UpdatedAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user);
    }

    public async Task DeleteAccountAsync(string email, DeleteAccountRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        if (!_passwordHasher.Verify(request.Password, user.Password))
        {
            throw new Exception("Invalid credentials");
        }

        user.IsDeleted = true;
        user.DeletedAt = DateTime.UtcNow;
        user.UpdatedAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user);
    }

    public async Task<IEnumerable<UserProfileResponse>> GetAllUsersAsync()
    {
        var users = await _userRepository.GetAllAsync();
        var responses = new List<UserProfileResponse>();

        foreach (var user in users)
        {
            var preferences = DeserializePreferences(user.PreferencesJson);
            var stats = new UserStats(0, 0, 0); // Simplified stats for list view
            responses.Add(new UserProfileResponse(
                user.Id, user.Email, user.Name ?? string.Empty, user.Bio ?? string.Empty,
                user.Phone, user.AvatarUrl, user.IsEmailVerified, preferences, stats, user.CreatedAt,
                user.Role ?? "User"
            ));
        }

        return responses;
    }

    public async Task UpdateUserRoleAsync(long userId, string newRole)
    {
        var user = await _userRepository.GetByIdAsync(userId)
                    ?? throw new Exception("User not found");

        user.Role = newRole;
        user.UpdatedAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user);
    }

    private static UserPreferences? DeserializePreferences(string? json)
    {
        if (string.IsNullOrEmpty(json)) return null;
        try { return JsonSerializer.Deserialize<UserPreferences>(json, _jsonOptions); }
        catch { return null; }
    }
}
