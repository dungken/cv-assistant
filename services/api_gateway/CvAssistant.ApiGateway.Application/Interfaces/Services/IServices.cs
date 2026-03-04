using CvAssistant.ApiGateway.Application.DTOs;

namespace CvAssistant.ApiGateway.Application.Interfaces.Services;

public interface IAuthService
{
    Task<AuthResponse> RegisterAsync(RegisterRequest request);
    Task<AuthResponse> LoginAsync(LoginRequest request);
}

public interface IUserService
{
    Task<UserProfileResponse> GetProfileAsync(string email);
    Task<UserProfileResponse> UpdateProfileAsync(string email, UpdateUserRequest request);
}

public interface IChatService
{
    Task<IEnumerable<SessionResponse>> GetSessionsAsync(string email);
    Task<SessionResponse> CreateSessionAsync(string email, string title);
    Task DeleteSessionAsync(long sessionId);
    Task<SessionResponse> UpdateTitleAsync(long sessionId, string title);
    Task<IEnumerable<MessageResponse>> GetMessagesAsync(long sessionId);
    Task SaveMessageAsync(long sessionId, SaveMessageRequest request);
}

public interface ICVHistoryService
{
    Task<IEnumerable<CVHistoryResponse>> GetHistoryAsync(string email);
    Task<CVHistoryResponse> SaveHistoryAsync(string email, SaveCVHistoryRequest request);
}
