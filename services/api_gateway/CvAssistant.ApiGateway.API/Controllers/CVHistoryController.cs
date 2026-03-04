using System.Security.Claims;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/cv-history")]
[Authorize]
public class CVHistoryController : ControllerBase
{
    private readonly ICVHistoryService _cvHistoryService;

    public CVHistoryController(ICVHistoryService cvHistoryService)
    {
        _cvHistoryService = cvHistoryService;
    }

    private string GetEmail() => User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;

    [HttpGet]
    public async Task<ActionResult<IEnumerable<CVHistoryResponse>>> GetHistory()
    {
        return Ok(await _cvHistoryService.GetHistoryAsync(GetEmail()));
    }

    [HttpPost]
    public async Task<ActionResult<CVHistoryResponse>> SaveHistory([FromBody] SaveCVHistoryRequest request)
    {
        return Ok(await _cvHistoryService.SaveHistoryAsync(GetEmail(), request));
    }
}
