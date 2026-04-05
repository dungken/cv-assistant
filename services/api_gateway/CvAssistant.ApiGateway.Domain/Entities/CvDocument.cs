namespace CvAssistant.ApiGateway.Domain.Entities;

public class CvDocument
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Template { get; set; }
    public string? TargetJd { get; set; }
    public int? AtsScore { get; set; }
    public int CurrentVersion { get; set; } = 1;

    public bool IsDeleted { get; set; }
    public DateTime? DeletedAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    // Navigation
    public User? User { get; set; }
    public ICollection<CvVersion> Versions { get; set; } = new List<CvVersion>();
}

public class CvVersion
{
    public long Id { get; set; }
    public long CvDocumentId { get; set; }
    public int VersionNumber { get; set; }
    public string DataJson { get; set; } = string.Empty;
    public string? Note { get; set; }
    public string? Tag { get; set; }
    public bool IsStarred { get; set; }
    public DateTime CreatedAt { get; set; }

    // Navigation
    public CvDocument? CvDocument { get; set; }
}
