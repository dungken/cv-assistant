using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Domain.Entities;
using CvAssistant.ApiGateway.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Repositories;

public class CvDocumentRepository : ICvDocumentRepository
{
    private readonly AppDbContext _context;

    public CvDocumentRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<CvDocument?> GetByIdAsync(long id)
    {
        return await _context.CvDocuments.FindAsync(id);
    }

    public async Task<CvDocument?> GetByIdWithVersionsAsync(long id)
    {
        return await _context.CvDocuments
            .Include(d => d.Versions.OrderByDescending(v => v.VersionNumber))
            .FirstOrDefaultAsync(d => d.Id == id);
    }

    public async Task<IEnumerable<CvDocument>> GetByUserIdAsync(long userId)
    {
        return await _context.CvDocuments
            .Include(d => d.Versions.OrderByDescending(v => v.VersionNumber))
            .Where(d => d.UserId == userId)
            .OrderByDescending(d => d.UpdatedAt)
            .ToListAsync();
    }

    public async Task<IEnumerable<CvDocument>> SearchAsync(long userId, string? query, string? template,
        DateTime? fromDate, DateTime? toDate, string sortBy, int page, int pageSize)
    {
        var q = _context.CvDocuments
            .Include(d => d.Versions.OrderByDescending(v => v.VersionNumber))
            .Where(d => d.UserId == userId);

        if (!string.IsNullOrWhiteSpace(query))
            q = q.Where(d => d.Name.ToLower().Contains(query.ToLower()) ||
                             (d.TargetJd != null && d.TargetJd.ToLower().Contains(query.ToLower())));

        if (!string.IsNullOrWhiteSpace(template))
            q = q.Where(d => d.Template == template);

        if (fromDate.HasValue)
            q = q.Where(d => d.CreatedAt >= fromDate.Value);

        if (toDate.HasValue)
            q = q.Where(d => d.CreatedAt <= toDate.Value);

        q = sortBy switch
        {
            "name" => q.OrderBy(d => d.Name),
            "created" => q.OrderByDescending(d => d.CreatedAt),
            _ => q.OrderByDescending(d => d.UpdatedAt)
        };

        return await q.Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();
    }

    public async Task<int> CountByUserIdAsync(long userId)
    {
        return await _context.CvDocuments.CountAsync(d => d.UserId == userId);
    }

    public async Task<CvDocument?> GetDeletedByIdAsync(long id)
    {
        return await _context.CvDocuments.IgnoreQueryFilters()
            .Include(d => d.Versions.OrderByDescending(v => v.VersionNumber))
            .FirstOrDefaultAsync(d => d.Id == id && d.IsDeleted);
    }

    public async Task AddAsync(CvDocument document)
    {
        _context.CvDocuments.Add(document);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(CvDocument document)
    {
        _context.CvDocuments.Update(document);
        await _context.SaveChangesAsync();
    }
}

public class CvVersionRepository : ICvVersionRepository
{
    private readonly AppDbContext _context;

    public CvVersionRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<CvVersion?> GetByIdAsync(long id)
    {
        return await _context.CvVersions.FindAsync(id);
    }

    public async Task<CvVersion?> GetByDocumentAndVersionAsync(long documentId, int versionNumber)
    {
        return await _context.CvVersions
            .FirstOrDefaultAsync(v => v.CvDocumentId == documentId && v.VersionNumber == versionNumber);
    }

    public async Task<IEnumerable<CvVersion>> GetByDocumentIdAsync(long documentId)
    {
        return await _context.CvVersions
            .Where(v => v.CvDocumentId == documentId)
            .OrderByDescending(v => v.VersionNumber)
            .ToListAsync();
    }

    public async Task AddAsync(CvVersion version)
    {
        _context.CvVersions.Add(version);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(CvVersion version)
    {
        _context.CvVersions.Update(version);
        await _context.SaveChangesAsync();
    }
}
