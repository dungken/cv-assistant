namespace CvAssistant.ApiGateway.Application.DTOs;

public record CreateFeedbackRequest(
    string? ItemId,
    string Type,
    int? Rating,
    string? Comment,
    string? CorrectionJson
);

public record FeedbackResponse(
    long Id,
    long UserId,
    string? UserName,
    string? ItemId,
    string Type,
    int? Rating,
    string? Comment,
    string? CorrectionJson,
    string? Sentiment,
    DateTime CreatedAt
);
