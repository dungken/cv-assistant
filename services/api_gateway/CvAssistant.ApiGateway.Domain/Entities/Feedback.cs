using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace CvAssistant.ApiGateway.Domain.Entities;

public class Feedback
{
    public long Id { get; set; }
    
    public long UserId { get; set; }
    
    [ForeignKey("UserId")]
    public User? User { get; set; }

    public string? ItemId { get; set; } // ID of the CV or Chat Session related to this feedback
    
    [Required]
    public string Type { get; set; } = "CV_Rating"; // CV_Rating, Chat_Like, Chat_Dislike, OCR_Correction

    public int? Rating { get; set; } // 1-5 for CVs

    public string? Comment { get; set; }

    public string? CorrectionJson { get; set; } // For RLHF data, store {Original, Corrected}

    public string? Sentiment { get; set; } // "positive", "negative", "neutral"

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
