namespace CvAssistant.ApiGateway.Application.DTOs;

public record UserProfileResponse(long Id, string Email, string Name, string Bio);
public record UpdateUserRequest(string? Name, string? Bio);
