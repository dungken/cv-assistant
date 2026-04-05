using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class CvTemplateService : ICvTemplateService
{
    private readonly ICvTemplateRepository _templateRepository;

    public CvTemplateService(ICvTemplateRepository templateRepository)
    {
        _templateRepository = templateRepository;
    }

    public async Task<CvTemplateResponse> GetByIdAsync(long id)
    {
        var template = await _templateRepository.GetByIdAsync(id)
                       ?? throw new Exception("Template not found");
        return MapToResponse(template);
    }

    public async Task<IEnumerable<CvTemplateResponse>> GetAllAsync(bool includeUnpublished = false)
    {
        var templates = await _templateRepository.GetAllAsync(includeUnpublished);
        return templates.Select(MapToResponse);
    }

    public async Task<IEnumerable<CvTemplateResponse>> GetByCategoryAsync(string category)
    {
        var templates = await _templateRepository.GetByCategoryAsync(category);
        return templates.Select(MapToResponse);
    }

    public async Task<CvTemplateResponse> CreateAsync(CreateCvTemplateRequest request)
    {
        var template = new CvTemplate
        {
            Name = request.Name,
            Description = request.Description,
            Category = request.Category,
            LayoutHtml = request.LayoutHtml,
            StylesCss = request.StylesCss,
            ConfigJson = request.ConfigJson,
            IsPublished = request.IsPublished,
            CreatedAt = DateTime.UtcNow
        };
        await _templateRepository.AddAsync(template);
        return MapToResponse(template);
    }

    public async Task<CvTemplateResponse> UpdateAsync(long id, UpdateCvTemplateRequest request)
    {
        var template = await _templateRepository.GetByIdAsync(id)
                       ?? throw new Exception("Template not found");

        if (request.Name != null) template.Name = request.Name;
        if (request.Description != null) template.Description = request.Description;
        if (request.Category != null) template.Category = request.Category;
        if (request.LayoutHtml != null) template.LayoutHtml = request.LayoutHtml;
        if (request.StylesCss != null) template.StylesCss = request.StylesCss;
        if (request.ConfigJson != null) template.ConfigJson = request.ConfigJson;
        if (request.IsPublished.HasValue) template.IsPublished = request.IsPublished.Value;
        if (request.IsArchived.HasValue) template.IsArchived = request.IsArchived.Value;

        template.UpdatedAt = DateTime.UtcNow;
        await _templateRepository.UpdateAsync(template);
        return MapToResponse(template);
    }

    public async Task DeleteAsync(long id)
    {
        await _templateRepository.DeleteAsync(id);
    }

    private static CvTemplateResponse MapToResponse(CvTemplate t)
    {
        return new CvTemplateResponse(
            t.Id, t.Name, t.Description, t.Category, t.ThumbnailUrl,
            t.LayoutHtml, t.StylesCss, t.ConfigJson, t.IsPublished, t.IsArchived,
            t.CreatedAt, t.UsageCount
        );
    }
}
