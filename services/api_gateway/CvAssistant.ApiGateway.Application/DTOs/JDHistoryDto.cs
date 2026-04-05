namespace CvAssistant.ApiGateway.Application.DTOs;

public record JDHistoryResponse(long Id, string Title, string Company, string InputMethod, DateTime CreatedAt);
public record SaveJDHistoryRequest(string? Title, string? Company, string? FileName, string? FileUrl, string? SourceUrl, string InputMethod, string ExtractionResult);
