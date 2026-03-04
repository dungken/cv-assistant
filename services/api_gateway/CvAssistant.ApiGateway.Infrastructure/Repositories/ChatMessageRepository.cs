using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class ChatMessageRepository : IChatMessageRepository
{
    private readonly AppDbContext _context;

    public ChatMessageRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<ChatMessage>> GetBySessionIdOrderByTimestampAscAsync(long sessionId)
    {
        return await _context.ChatMessages
            .Where(m => m.SessionId == sessionId)
            .OrderBy(m => m.Timestamp)
            .ToListAsync();
    }

    public async Task AddAsync(ChatMessage message)
    {
        _context.ChatMessages.Add(message);
        await _context.SaveChangesAsync();
    }
}
