using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/collector")]
[Authorize]
public class CollectorController : ControllerBase
{
    private readonly ICollectorService _collectorService;

    public CollectorController(ICollectorService collectorService)
    {
        _collectorService = collectorService;
    }

    [HttpGet("{sessionId}")]
    public async Task<ActionResult<CollectorProgressResponse>> GetProgress(long sessionId)
    {
        var progress = await _collectorService.GetProgressAsync(sessionId);
        return Ok(progress);
    }

    [HttpPost("{sessionId}")]
    public async Task<ActionResult<CollectorProgressResponse>> UpdateProgress(long sessionId, [FromBody] UpdateCollectorProgressRequest request)
    {
        try
        {
            var progress = await _collectorService.UpdateProgressAsync(sessionId, request);
            return Ok(progress);
        }
        catch (Exception ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }
}
