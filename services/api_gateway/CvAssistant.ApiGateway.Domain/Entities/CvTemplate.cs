using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace CvAssistant.ApiGateway.Domain.Entities;

public class CvTemplate
{
    public long Id { get; set; }
    
    [Required]
    [MaxLength(200)]
    public string Name { get; set; } = string.Empty;
    
    public string? Description { get; set; }
    
    public string? Category { get; set; } // e.g., "Technology", "Creative"
    
    public string? ThumbnailUrl { get; set; }
    
    [Required]
    public string LayoutHtml { get; set; } = string.Empty;
    
    [Required]
    public string StylesCss { get; set; } = string.Empty;
    
    public string? ConfigJson { get; set; } // JSON with dynamic section configs
    
    public bool IsPublished { get; set; } = false;
    
    public bool IsArchived { get; set; } = false;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; set; }

    // Stats
    public int UsageCount { get; set; } = 0;
}
