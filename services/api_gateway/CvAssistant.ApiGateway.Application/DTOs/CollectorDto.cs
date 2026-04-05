namespace CvAssistant.ApiGateway.Application.DTOs;

public class CollectorProgressResponse
{
    public long Id { get; set; }
    public long SessionId { get; set; }
    public int CurrentStep { get; set; }
    public string DataJson { get; set; } = "{}";
    public bool IsComplete { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class UpdateCollectorProgressRequest
{
    public int CurrentStep { get; set; }
    public string DataJson { get; set; } = "{}";
    public bool IsComplete { get; set; }
}
