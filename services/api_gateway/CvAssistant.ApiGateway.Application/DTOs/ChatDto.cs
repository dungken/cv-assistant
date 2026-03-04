namespace CvAssistant.ApiGateway.Application.DTOs;

public record SessionResponse(long Id, string Title, DateTime UpdatedAt);
public record CreateSessionRequest(string Title);
public record MessageResponse(long Id, string Role, string Content, DateTime Timestamp);
public record SaveMessageRequest(string Role, string Content);
