namespace CvAssistant.ApiGateway.Application.DTOs;

public record CVHistoryResponse(long Id, string FileName, string FileUrl, DateTime UploadedAt);
public record SaveCVHistoryRequest(string FileName, string FileUrl, string ExtractionResult);
