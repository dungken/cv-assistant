namespace CvAssistant.ApiGateway.Domain.Entities;

public class CVHistory
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public string? FileName { get; set; }
    public string? FileUrl { get; set; }
    public string? ExtractionResult { get; set; }
    public DateTime UploadedAt { get; set; }

    // Navigation property
    public User? User { get; set; }
}
