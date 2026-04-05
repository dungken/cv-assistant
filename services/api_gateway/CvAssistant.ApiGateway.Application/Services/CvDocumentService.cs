using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class CvDocumentService : ICvDocumentService
{
    private readonly ICvDocumentRepository _documentRepository;
    private readonly ICvVersionRepository _versionRepository;
    private readonly IUserRepository _userRepository;

    public CvDocumentService(ICvDocumentRepository documentRepository, ICvVersionRepository versionRepository, IUserRepository userRepository)
    {
        _documentRepository = documentRepository;
        _versionRepository = versionRepository;
        _userRepository = userRepository;
    }

    public async Task<CvDocumentResponse> CreateAsync(string email, CreateCvDocumentRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var document = new CvDocument
        {
            UserId = user.Id,
            Name = request.Name,
            Template = request.Template,
            TargetJd = request.TargetJd,
            CurrentVersion = 1,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };
        await _documentRepository.AddAsync(document);

        var version = new CvVersion
        {
            CvDocumentId = document.Id,
            VersionNumber = 1,
            DataJson = request.DataJson,
            Note = request.Note ?? "Initial version",
            CreatedAt = DateTime.UtcNow
        };
        await _versionRepository.AddAsync(version);

        return await GetByIdAsync(email, document.Id);
    }

    public async Task<CvDocumentResponse> GetByIdAsync(string email, long id)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetByIdWithVersionsAsync(id)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        return MapToResponse(doc);
    }

    public async Task<IEnumerable<CvDocumentResponse>> ListAsync(string email, CvSearchRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var docs = await _documentRepository.SearchAsync(
            user.Id, request.Query, request.Template,
            request.FromDate, request.ToDate,
            request.SortBy, request.Page, request.PageSize);

        return docs.Select(MapToResponse);
    }

    public async Task<CvDocumentResponse> UpdateAsync(string email, long id, UpdateCvDocumentRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetByIdAsync(id)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        if (request.Name != null) doc.Name = request.Name;
        if (request.Template != null) doc.Template = request.Template;
        if (request.TargetJd != null) doc.TargetJd = request.TargetJd;
        if (request.AtsScore.HasValue) doc.AtsScore = request.AtsScore;
        doc.UpdatedAt = DateTime.UtcNow;

        await _documentRepository.UpdateAsync(doc);
        return await GetByIdAsync(email, id);
    }

    public async Task DeleteAsync(string email, long id)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetByIdAsync(id)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        doc.IsDeleted = true;
        doc.DeletedAt = DateTime.UtcNow;
        await _documentRepository.UpdateAsync(doc);
    }

    public async Task<CvDocumentResponse> RestoreAsync(string email, long id)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetDeletedByIdAsync(id)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        if (doc.DeletedAt.HasValue && doc.DeletedAt.Value.AddDays(30) < DateTime.UtcNow)
            throw new Exception("Recovery period expired");

        doc.IsDeleted = false;
        doc.DeletedAt = null;
        await _documentRepository.UpdateAsync(doc);

        return MapToResponse(doc);
    }

    public async Task<CvVersionDetailResponse> CreateVersionAsync(string email, long documentId, CreateCvVersionRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetByIdAsync(documentId)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        var newVersionNumber = doc.CurrentVersion + 1;
        var version = new CvVersion
        {
            CvDocumentId = documentId,
            VersionNumber = newVersionNumber,
            DataJson = request.DataJson,
            Note = request.Note,
            CreatedAt = DateTime.UtcNow
        };
        await _versionRepository.AddAsync(version);

        doc.CurrentVersion = newVersionNumber;
        doc.UpdatedAt = DateTime.UtcNow;
        await _documentRepository.UpdateAsync(doc);

        return new CvVersionDetailResponse(version.Id, version.VersionNumber, version.DataJson, version.Note, version.Tag, version.IsStarred, version.CreatedAt);
    }

    public async Task<CvVersionDetailResponse> GetVersionAsync(long documentId, long versionId)
    {
        var version = await _versionRepository.GetByIdAsync(versionId)
                      ?? throw new Exception("Version not found");

        if (version.CvDocumentId != documentId) throw new Exception("Version does not belong to this document");

        return new CvVersionDetailResponse(version.Id, version.VersionNumber, version.DataJson, version.Note, version.Tag, version.IsStarred, version.CreatedAt);
    }

    public async Task UpdateVersionAsync(long versionId, UpdateCvVersionRequest request)
    {
        var version = await _versionRepository.GetByIdAsync(versionId)
                      ?? throw new Exception("Version not found");

        if (request.Note != null) version.Note = request.Note;
        if (request.Tag != null) version.Tag = request.Tag;
        if (request.IsStarred.HasValue) version.IsStarred = request.IsStarred.Value;

        await _versionRepository.UpdateAsync(version);
    }

    public async Task<CvDiffResponse> DiffAsync(long documentId, int versionA, int versionB)
    {
        var va = await _versionRepository.GetByDocumentAndVersionAsync(documentId, versionA)
                 ?? throw new Exception($"Version {versionA} not found");

        var vb = await _versionRepository.GetByDocumentAndVersionAsync(documentId, versionB)
                 ?? throw new Exception($"Version {versionB} not found");

        var oldVersion = new CvVersionDetailResponse(va.Id, va.VersionNumber, va.DataJson, va.Note, va.Tag, va.IsStarred, va.CreatedAt);
        var newVersion = new CvVersionDetailResponse(vb.Id, vb.VersionNumber, vb.DataJson, vb.Note, vb.Tag, vb.IsStarred, vb.CreatedAt);

        return new CvDiffResponse(oldVersion, newVersion);
    }

    public async Task<CvDocumentResponse> RestoreVersionAsync(string email, long documentId, int versionNumber)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var doc = await _documentRepository.GetByIdAsync(documentId)
                  ?? throw new Exception("CV document not found");

        if (doc.UserId != user.Id) throw new Exception("Access denied");

        var sourceVersion = await _versionRepository.GetByDocumentAndVersionAsync(documentId, versionNumber)
                            ?? throw new Exception($"Version {versionNumber} not found");

        var newVersionNumber = doc.CurrentVersion + 1;
        var restoredVersion = new CvVersion
        {
            CvDocumentId = documentId,
            VersionNumber = newVersionNumber,
            DataJson = sourceVersion.DataJson,
            Note = $"Restored from v{versionNumber}",
            CreatedAt = DateTime.UtcNow
        };
        await _versionRepository.AddAsync(restoredVersion);

        doc.CurrentVersion = newVersionNumber;
        doc.UpdatedAt = DateTime.UtcNow;
        await _documentRepository.UpdateAsync(doc);

        return await GetByIdAsync(email, documentId);
    }

    private static CvDocumentResponse MapToResponse(CvDocument doc)
    {
        return new CvDocumentResponse(
            doc.Id, doc.Name, doc.Template, doc.TargetJd, doc.AtsScore,
            doc.CurrentVersion, doc.CreatedAt, doc.UpdatedAt,
            doc.Versions.Select(v => new CvVersionResponse(v.Id, v.VersionNumber, v.Note, v.Tag, v.IsStarred, v.CreatedAt)).ToList()
        );
    }
}
