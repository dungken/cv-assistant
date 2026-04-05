namespace CvAssistant.ApiGateway.Domain.Entities;

public class JDHistory
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public string? Title { get; set; }
    public string? Company { get; set; }
    public string? FileName { get; set; }
    public string? FileUrl { get; set; }
    public string? SourceUrl { get; set; }
    public string? InputMethod { get; set; } // "file", "text", "url"
    public string? ExtractionResult { get; set; }
    public DateTime CreatedAt { get; set; }

    // Navigation property
    public User? User { get; set; }
}
