using System.Security.Claims;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/feedback")]
[Authorize]
public class FeedbackController : ControllerBase
{
    private readonly IFeedbackService _feedbackService;

    public FeedbackController(IFeedbackService feedbackService)
    {
        _feedbackService = feedbackService;
    }

    [HttpPost]
    public async Task<ActionResult<FeedbackResponse>> Create(CreateFeedbackRequest request)
    {
        var email = User.FindFirstValue(ClaimTypes.Email) ?? throw new Exception("Unauthorized");
        var feedback = await _feedbackService.CreateAsync(email, request);
        return Ok(feedback);
    }

    [HttpGet("my")]
    public async Task<ActionResult<IEnumerable<FeedbackResponse>>> GetMyFeedback()
    {
        var email = User.FindFirstValue(ClaimTypes.Email) ?? throw new Exception("Unauthorized");
        var feedbacks = await _feedbackService.GetByUserIdAsync(email);
        return Ok(feedbacks);
    }

    [HttpGet("all")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<IEnumerable<FeedbackResponse>>> GetAll()
    {
        var feedbacks = await _feedbackService.GetAllAsync();
        return Ok(feedbacks);
    }

    [HttpGet("type/{type}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<IEnumerable<FeedbackResponse>>> GetByType(string type)
    {
        var feedbacks = await _feedbackService.GetByTypeAsync(type);
        return Ok(feedbacks);
    }
}
