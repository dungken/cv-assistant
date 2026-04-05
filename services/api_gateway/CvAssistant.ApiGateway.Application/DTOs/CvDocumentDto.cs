namespace CvAssistant.ApiGateway.Application.DTOs;

public record CvDocumentResponse(
    long Id,
    string Name,
    string? Template,
    string? TargetJd,
    int? AtsScore,
    int CurrentVersion,
    DateTime CreatedAt,
    DateTime UpdatedAt,
    List<CvVersionResponse> Versions
);

public record CvVersionResponse(
    long Id,
    int VersionNumber,
    string? Note,
    string? Tag,
    bool IsStarred,
    DateTime CreatedAt
);

public record CvVersionDetailResponse(
    long Id,
    int VersionNumber,
    string DataJson,
    string? Note,
    string? Tag,
    bool IsStarred,
    DateTime CreatedAt
);

public record CreateCvDocumentRequest(string Name, string? Template, string? TargetJd, string DataJson, string? Note);
public record CreateCvVersionRequest(string DataJson, string? Note);
public record UpdateCvDocumentRequest(string? Name, string? Template, string? TargetJd, int? AtsScore);
public record UpdateCvVersionRequest(string? Note, string? Tag, bool? IsStarred);
public record CvDiffResponse(CvVersionDetailResponse OldVersion, CvVersionDetailResponse NewVersion);
public record CvSearchRequest(string? Query, string? Template, DateTime? FromDate, DateTime? ToDate, string SortBy = "updated", int Page = 1, int PageSize = 20);
