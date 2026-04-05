namespace CvAssistant.ApiGateway.Application.DTOs;

public record UserProfileResponse(
    long Id,
    string Email,
    string Name,
    string Bio,
    string? Phone,
    string? AvatarUrl,
    bool IsEmailVerified,
    UserPreferences? Preferences,
    UserStats? Stats,
    DateTime CreatedAt,
    string Role
);

public record UserPreferences(
    string? Language,
    string? Industry,
    string? CareerLevel
);

public record UserStats(
    int CvsCreated,
    int AnalysesDone,
    int CoursesBookmarked
);

public record UpdateUserRequest(string? Name, string? Bio, string? Phone, UserPreferences? Preferences);
public record ChangePasswordRequest(string OldPassword, string NewPassword);
public record DeleteAccountRequest(string Password);
