using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class FeedbackService : IFeedbackService
{
    private readonly IFeedbackRepository _feedbackRepository;
    private readonly IUserRepository _userRepository;

    public FeedbackService(IFeedbackRepository feedbackRepository, IUserRepository userRepository)
    {
        _feedbackRepository = feedbackRepository;
        _userRepository = userRepository;
    }

    public async Task<FeedbackResponse> GetByIdAsync(long id)
    {
        var feedback = await _feedbackRepository.GetByIdAsync(id)
                       ?? throw new Exception("Feedback not found");
        return MapToResponse(feedback);
    }

    public async Task<IEnumerable<FeedbackResponse>> GetByUserIdAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");
        var feedbacks = await _feedbackRepository.GetByUserIdAsync(user.Id);
        return feedbacks.Select(MapToResponse);
    }

    public async Task<IEnumerable<FeedbackResponse>> GetByTypeAsync(string type)
    {
        var feedbacks = await _feedbackRepository.GetByTypeAsync(type);
        return feedbacks.Select(MapToResponse);
    }

    public async Task<IEnumerable<FeedbackResponse>> GetAllAsync()
    {
        var feedbacks = await _feedbackRepository.GetAllAsync();
        return feedbacks.Select(MapToResponse);
    }

    public async Task<FeedbackResponse> CreateAsync(string email, CreateFeedbackRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        var feedback = new Feedback
        {
            UserId = user.Id,
            ItemId = request.ItemId,
            Type = request.Type,
            Rating = request.Rating,
            Comment = request.Comment,
            CorrectionJson = request.CorrectionJson,
            CreatedAt = DateTime.UtcNow
        };

        // Simple sentiment analysis (stub)
        if (request.Rating >= 4) feedback.Sentiment = "positive";
        else if (request.Rating <= 2) feedback.Sentiment = "negative";
        else feedback.Sentiment = "neutral";

        await _feedbackRepository.AddAsync(feedback);
        feedback.User = user; // For mapping
        return MapToResponse(feedback);
    }

    private static FeedbackResponse MapToResponse(Feedback f)
    {
        return new FeedbackResponse(
            f.Id, f.UserId, f.User?.Name, f.ItemId, f.Type,
            f.Rating, f.Comment, f.CorrectionJson, f.Sentiment, f.CreatedAt
        );
    }
}
