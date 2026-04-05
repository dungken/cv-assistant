namespace CvAssistant.ApiGateway.Domain.Entities;

public class ChatSession
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public string Title { get; set; } = "New Conversation";
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    // Navigation property
    public User? User { get; set; }
    public ICollection<ChatMessage> Messages { get; set; } = new List<ChatMessage>();
    public CollectorProgress? CollectorProgress { get; set; }
}
