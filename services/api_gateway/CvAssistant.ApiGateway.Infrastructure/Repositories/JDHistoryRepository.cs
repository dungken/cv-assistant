using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class JDHistoryRepository : IJDHistoryRepository
{
    private readonly AppDbContext _context;

    public JDHistoryRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<JDHistory>> GetByUserIdOrderByCreatedDescAsync(long userId)
    {
        return await _context.JDHistories
            .Where(h => h.UserId == userId)
            .OrderByDescending(h => h.CreatedAt)
            .ToListAsync();
    }

    public async Task<JDHistory?> GetByIdAsync(long id)
    {
        return await _context.JDHistories.FindAsync(id);
    }

    public async Task AddAsync(JDHistory history)
    {
        _context.JDHistories.Add(history);
        await _context.SaveChangesAsync();
    }

    public async Task DeleteAsync(long id)
    {
        var history = await _context.JDHistories.FindAsync(id);
        if (history != null)
        {
            _context.JDHistories.Remove(history);
            await _context.SaveChangesAsync();
        }
    }
}
