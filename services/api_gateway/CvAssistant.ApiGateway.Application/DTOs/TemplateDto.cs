namespace CvAssistant.ApiGateway.Application.DTOs;

public record CreateCvTemplateRequest(
    string Name,
    string? Description,
    string? Category,
    string LayoutHtml,
    string StylesCss,
    string? ConfigJson,
    bool IsPublished
);

public record UpdateCvTemplateRequest(
    string? Name,
    string? Description,
    string? Category,
    string? LayoutHtml,
    string? StylesCss,
    string? ConfigJson,
    bool? IsPublished,
    bool? IsArchived
);

public record CvTemplateResponse(
    long Id,
    string Name,
    string? Description,
    string? Category,
    string? ThumbnailUrl,
    string LayoutHtml,
    string StylesCss,
    string? ConfigJson,
    bool IsPublished,
    bool IsArchived,
    DateTime CreatedAt,
    int UsageCount
);
