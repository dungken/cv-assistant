namespace CvAssistant.ApiGateway.Domain.Entities;

public class CollectorProgress
{
    public long Id { get; set; }
    public long SessionId { get; set; }
    public int CurrentStep { get; set; } = 1; // 1: Personal, 2: Edu, 3: Exp, 4: Skills, 5: Proj, 6: Cert
    public string DataJson { get; set; } = "{}";
    public bool IsComplete { get; set; } = false;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation property
    public ChatSession? Session { get; set; }
}
