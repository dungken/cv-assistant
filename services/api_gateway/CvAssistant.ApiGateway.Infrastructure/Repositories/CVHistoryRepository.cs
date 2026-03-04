using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class CVHistoryRepository : ICVHistoryRepository
{
    private readonly AppDbContext _context;

    public CVHistoryRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<CVHistory>> GetByUserIdOrderByUploadedDescAsync(long userId)
    {
        return await _context.CVHistories
            .Where(h => h.UserId == userId)
            .OrderByDescending(h => h.UploadedAt)
            .ToListAsync();
    }

    public async Task AddAsync(CVHistory history)
    {
        _context.CVHistories.Add(history);
        await _context.SaveChangesAsync();
    }
}
