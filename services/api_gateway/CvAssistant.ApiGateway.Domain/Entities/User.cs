namespace CvAssistant.ApiGateway.Domain.Entities;

public class User
{
    public long Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string? Name { get; set; }
    public string? Bio { get; set; }
    
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    public ICollection<ChatSession> ChatSessions { get; set; } = new List<ChatSession>();
    public ICollection<CVHistory> CVHistories { get; set; } = new List<CVHistory>();
}
