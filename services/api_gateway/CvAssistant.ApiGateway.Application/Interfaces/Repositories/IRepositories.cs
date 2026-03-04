using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Interfaces.Repositories;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(long id);
    Task<User?> GetByEmailAsync(string email);
    Task<bool> ExistsByEmailAsync(string email);
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
    Task AddAsync(CVHistory history);
}
