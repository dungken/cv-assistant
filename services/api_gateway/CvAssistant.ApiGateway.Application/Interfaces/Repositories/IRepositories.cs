using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Interfaces.Repositories;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(long id);
    Task<User?> GetByEmailAsync(string email);
    Task<User?> GetByEmailIncludeDeletedAsync(string email);
    Task<User?> GetByRefreshTokenAsync(string refreshToken);
    Task<User?> GetByEmailVerificationTokenAsync(string token);
    Task<User?> GetByPasswordResetTokenAsync(string email, string token);
    Task<bool> ExistsByEmailAsync(string email);
    Task<IEnumerable<User>> GetAllAsync();
    Task AddAsync(User user);
    Task UpdateAsync(User user);
}

public interface IChatSessionRepository
{
    Task<ChatSession?> GetByIdAsync(long id);
    Task<IEnumerable<ChatSession>> GetByUserIdOrderByUpdatedDescAsync(long userId);
    Task AddAsync(ChatSession session);
    Task UpdateAsync(ChatSession session);
    Task DeleteAsync(long id);
}

public interface IChatMessageRepository
{
    Task<IEnumerable<ChatMessage>> GetBySessionIdOrderByTimestampAscAsync(long sessionId);
    Task AddAsync(ChatMessage message);
}

public interface ICVHistoryRepository
{
    Task<IEnumerable<CVHistory>> GetByUserIdOrderByUploadedDescAsync(long userId);
    Task<int> CountByUserIdAsync(long userId);
    Task AddAsync(CVHistory history);
}

public interface ICollectorRepository
{
    Task<CollectorProgress?> GetBySessionIdAsync(long sessionId);
    Task AddAsync(CollectorProgress progress);
    Task UpdateAsync(CollectorProgress progress);
}

public interface IJDHistoryRepository
{
    Task<IEnumerable<JDHistory>> GetByUserIdOrderByCreatedDescAsync(long userId);
    Task<JDHistory?> GetByIdAsync(long id);
    Task AddAsync(JDHistory history);
    Task DeleteAsync(long id);
}

public interface ICvDocumentRepository
{
    Task<CvDocument?> GetByIdAsync(long id);
    Task<CvDocument?> GetByIdWithVersionsAsync(long id);
    Task<IEnumerable<CvDocument>> GetByUserIdAsync(long userId);
    Task<IEnumerable<CvDocument>> SearchAsync(long userId, string? query, string? template, DateTime? fromDate, DateTime? toDate, string sortBy, int page, int pageSize);
    Task<int> CountByUserIdAsync(long userId);
    Task<CvDocument?> GetDeletedByIdAsync(long id);
    Task AddAsync(CvDocument document);
    Task UpdateAsync(CvDocument document);
}

public interface ICvVersionRepository
{
    Task<CvVersion?> GetByIdAsync(long id);
    Task<CvVersion?> GetByDocumentAndVersionAsync(long documentId, int versionNumber);
    Task<IEnumerable<CvVersion>> GetByDocumentIdAsync(long documentId);
    Task AddAsync(CvVersion version);
    Task UpdateAsync(CvVersion version);
}

public interface ICvTemplateRepository
{
    Task<CvTemplate?> GetByIdAsync(long id);
    Task<IEnumerable<CvTemplate>> GetAllAsync(bool includeUnpublished = false);
    Task<IEnumerable<CvTemplate>> GetByCategoryAsync(string category);
    Task AddAsync(CvTemplate template);
    Task UpdateAsync(CvTemplate template);
    Task DeleteAsync(long id);
}

public interface IFeedbackRepository
{
    Task<Feedback?> GetByIdAsync(long id);
    Task<IEnumerable<Feedback>> GetByUserIdAsync(long userId);
    Task<IEnumerable<Feedback>> GetByTypeAsync(string type);
    Task<IEnumerable<Feedback>> GetAllAsync();
    Task AddAsync(Feedback feedback);
}
