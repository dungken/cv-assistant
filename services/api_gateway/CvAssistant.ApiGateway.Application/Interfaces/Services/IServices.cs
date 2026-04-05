using CvAssistant.ApiGateway.Application.DTOs;

namespace CvAssistant.ApiGateway.Application.Interfaces.Services;

public interface IAuthService
{
    Task<AuthResponse> RegisterAsync(RegisterRequest request);
    Task<AuthResponse> LoginAsync(LoginRequest request);
    Task<AuthResponse> RefreshTokenAsync(RefreshTokenRequest request);
    Task VerifyEmailAsync(VerifyEmailRequest request);
    Task ForgotPasswordAsync(ForgotPasswordRequest request);
    Task ResetPasswordAsync(ResetPasswordRequest request);
}

public interface IUserService
{
    Task<UserProfileResponse> GetProfileAsync(string email);
    Task<UserProfileResponse> UpdateProfileAsync(string email, UpdateUserRequest request);
    Task<UserProfileResponse> UploadAvatarAsync(string email, Stream fileStream, string fileName);
    Task ChangePasswordAsync(string email, ChangePasswordRequest request);
    Task DeleteAccountAsync(string email, DeleteAccountRequest request);
    Task<IEnumerable<UserProfileResponse>> GetAllUsersAsync();
    Task UpdateUserRoleAsync(long userId, string newRole);
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

public interface ICollectorService
{
    Task<CollectorProgressResponse?> GetProgressAsync(long sessionId);
    Task<CollectorProgressResponse> UpdateProgressAsync(long sessionId, UpdateCollectorProgressRequest request);
}

public interface IJDHistoryService
{
    Task<IEnumerable<JDHistoryResponse>> GetHistoryAsync(string email);
    Task<JDHistoryResponse> SaveHistoryAsync(string email, SaveJDHistoryRequest request);
    Task DeleteHistoryAsync(long id);
}

public interface ICvDocumentService
{
    Task<CvDocumentResponse> CreateAsync(string email, CreateCvDocumentRequest request);
    Task<CvDocumentResponse> GetByIdAsync(string email, long id);
    Task<IEnumerable<CvDocumentResponse>> ListAsync(string email, CvSearchRequest request);
    Task<CvDocumentResponse> UpdateAsync(string email, long id, UpdateCvDocumentRequest request);
    Task DeleteAsync(string email, long id);
    Task<CvDocumentResponse> RestoreAsync(string email, long id);
    Task<CvVersionDetailResponse> CreateVersionAsync(string email, long documentId, CreateCvVersionRequest request);
    Task<CvVersionDetailResponse> GetVersionAsync(long documentId, long versionId);
    Task UpdateVersionAsync(long versionId, UpdateCvVersionRequest request);
    Task<CvDiffResponse> DiffAsync(long documentId, int versionA, int versionB);
    Task<CvDocumentResponse> RestoreVersionAsync(string email, long documentId, int versionNumber);
}

public interface ICvTemplateService
{
    Task<CvTemplateResponse> GetByIdAsync(long id);
    Task<IEnumerable<CvTemplateResponse>> GetAllAsync(bool includeUnpublished = false);
    Task<IEnumerable<CvTemplateResponse>> GetByCategoryAsync(string category);
    Task<CvTemplateResponse> CreateAsync(CreateCvTemplateRequest request);
    Task<CvTemplateResponse> UpdateAsync(long id, UpdateCvTemplateRequest request);
    Task DeleteAsync(long id);
}

public interface IFeedbackService
{
    Task<FeedbackResponse> GetByIdAsync(long id);
    Task<IEnumerable<FeedbackResponse>> GetByUserIdAsync(string email);
    Task<IEnumerable<FeedbackResponse>> GetByTypeAsync(string type);
    Task<IEnumerable<FeedbackResponse>> GetAllAsync();
    Task<FeedbackResponse> CreateAsync(string email, CreateFeedbackRequest request);
}
