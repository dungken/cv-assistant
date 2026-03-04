using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class ChatService : IChatService
{
    private readonly IChatSessionRepository _sessionRepository;
    private readonly IChatMessageRepository _messageRepository;
    private readonly IUserRepository _userRepository;

    public ChatService(IChatSessionRepository sessionRepository, IChatMessageRepository messageRepository, IUserRepository userRepository)
    {
        _sessionRepository = sessionRepository;
        _messageRepository = messageRepository;
        _userRepository = userRepository;
    }

    public async Task<IEnumerable<SessionResponse>> GetSessionsAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");
        var sessions = await _sessionRepository.GetByUserIdOrderByUpdatedDescAsync(user.Id);
        
        return sessions.Select(s => new SessionResponse(s.Id, s.Title, s.UpdatedAt));
    }

    public async Task<SessionResponse> CreateSessionAsync(string email, string title)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");
        var session = new ChatSession
        {
            UserId = user.Id,
            Title = string.IsNullOrWhiteSpace(title) ? "New Conversation" : title,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };
        
        await _sessionRepository.AddAsync(session);
        return new SessionResponse(session.Id, session.Title, session.UpdatedAt);
    }

    public async Task DeleteSessionAsync(long sessionId)
    {
        await _sessionRepository.DeleteAsync(sessionId);
    }

    public async Task<SessionResponse> UpdateTitleAsync(long sessionId, string title)
    {
        var session = await _sessionRepository.GetByIdAsync(sessionId) ?? throw new Exception("Session not found");
        session.Title = title;
        session.UpdatedAt = DateTime.UtcNow;
        
        await _sessionRepository.UpdateAsync(session);
        return new SessionResponse(session.Id, session.Title, session.UpdatedAt);
    }

    public async Task<IEnumerable<MessageResponse>> GetMessagesAsync(long sessionId)
    {
        var session = await _sessionRepository.GetByIdAsync(sessionId) ?? throw new Exception("Session not found");
        var messages = await _messageRepository.GetBySessionIdOrderByTimestampAscAsync(session.Id);
        
        return messages.Select(m => new MessageResponse(m.Id, m.Role, m.Content, m.Timestamp));
    }

    public async Task SaveMessageAsync(long sessionId, SaveMessageRequest request)
    {
        var session = await _sessionRepository.GetByIdAsync(sessionId) ?? throw new Exception("Session not found");
        
        var message = new ChatMessage
        {
            SessionId = session.Id,
            Role = request.Role,
            Content = request.Content,
            Timestamp = DateTime.UtcNow
        };
        
        await _messageRepository.AddAsync(message);
        
        session.UpdatedAt = DateTime.UtcNow;
        await _sessionRepository.UpdateAsync(session);
    }
}
