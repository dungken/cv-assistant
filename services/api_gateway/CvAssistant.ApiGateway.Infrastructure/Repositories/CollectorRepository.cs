using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class CollectorRepository : ICollectorRepository
{
    private readonly AppDbContext _context;

    public CollectorRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<CollectorProgress?> GetBySessionIdAsync(long sessionId)
    {
        return await _context.CollectorProgresses
            .FirstOrDefaultAsync(p => p.SessionId == sessionId);
    }

    public async Task AddAsync(CollectorProgress progress)
    {
        _context.CollectorProgresses.Add(progress);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(CollectorProgress progress)
    {
        progress.UpdatedAt = DateTime.UtcNow;
        _context.CollectorProgresses.Update(progress);
        await _context.SaveChangesAsync();
    }
}
