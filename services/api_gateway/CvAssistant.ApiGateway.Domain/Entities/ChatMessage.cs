namespace CvAssistant.ApiGateway.Domain.Entities;

public class ChatMessage
{
    public long Id { get; set; }
    public long SessionId { get; set; }
    public string Role { get; set; } = string.Empty; // 'user' or 'assistant'
    public string Content { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }

    // Navigation property
    public ChatSession? Session { get; set; }
}
