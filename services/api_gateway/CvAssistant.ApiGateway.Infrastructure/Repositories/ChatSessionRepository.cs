using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class ChatSessionRepository : IChatSessionRepository
{
    private readonly AppDbContext _context;

    public ChatSessionRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<ChatSession?> GetByIdAsync(long id)
    {
        return await _context.ChatSessions.FindAsync(id);
    }

    public async Task<IEnumerable<ChatSession>> GetByUserIdOrderByUpdatedDescAsync(long userId)
    {
        return await _context.ChatSessions
            .Where(s => s.UserId == userId)
            .OrderByDescending(s => s.UpdatedAt)
            .ToListAsync();
    }

    public async Task AddAsync(ChatSession session)
    {
        _context.ChatSessions.Add(session);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(ChatSession session)
    {
        _context.ChatSessions.Update(session);
        await _context.SaveChangesAsync();
    }

    public async Task DeleteAsync(long id)
    {
        var session = await GetByIdAsync(id);
        if (session != null)
        {
            _context.ChatSessions.Remove(session);
            await _context.SaveChangesAsync();
        }
    }
}
