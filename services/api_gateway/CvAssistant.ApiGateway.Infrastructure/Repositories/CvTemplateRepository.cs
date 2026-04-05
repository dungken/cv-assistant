using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class CvTemplateRepository : ICvTemplateRepository
{
    private readonly AppDbContext _context;

    public CvTemplateRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<CvTemplate?> GetByIdAsync(long id)
    {
        return await _context.CvTemplates.FindAsync(id);
    }

    public async Task<IEnumerable<CvTemplate>> GetAllAsync(bool includeUnpublished = false)
    {
        var query = _context.CvTemplates.AsQueryable();
        if (!includeUnpublished)
        {
            query = query.Where(t => t.IsPublished && !t.IsArchived);
        }
        return await query.OrderByDescending(t => t.CreatedAt).ToListAsync();
    }

    public async Task<IEnumerable<CvTemplate>> GetByCategoryAsync(string category)
    {
        return await _context.CvTemplates
            .Where(t => t.Category == category && t.IsPublished && !t.IsArchived)
            .OrderByDescending(t => t.UsageCount)
            .ToListAsync();
    }

    public async Task AddAsync(CvTemplate template)
    {
        template.CreatedAt = DateTime.UtcNow;
        _context.CvTemplates.Add(template);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(CvTemplate template)
    {
        template.UpdatedAt = DateTime.UtcNow;
        _context.CvTemplates.Update(template);
        await _context.SaveChangesAsync();
    }

    public async Task DeleteAsync(long id)
    {
        var template = await _context.CvTemplates.FindAsync(id);
        if (template != null)
        {
            _context.CvTemplates.Remove(template);
            await _context.SaveChangesAsync();
        }
    }
}
