using System.Security.Claims;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/chats")]
[Authorize]
public class ChatController : ControllerBase
{
    private readonly IChatService _chatService;

    public ChatController(IChatService chatService)
    {
        _chatService = chatService;
    }

    private string GetEmail() => User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;

    [HttpGet]
    public async Task<ActionResult<IEnumerable<SessionResponse>>> GetSessions()
    {
        return Ok(await _chatService.GetSessionsAsync(GetEmail()));
    }

    [HttpPost]
    public async Task<ActionResult<SessionResponse>> CreateSession([FromBody] CreateSessionRequest request)
    {
        return Ok(await _chatService.CreateSessionAsync(GetEmail(), request.Title));
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<SessionResponse>> UpdateTitle(long id, [FromBody] CreateSessionRequest request)
    {
        return Ok(await _chatService.UpdateTitleAsync(id, request.Title));
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteSession(long id)
    {
        await _chatService.DeleteSessionAsync(id);
        return Ok();
    }

    [HttpGet("{id}/messages")]
    public async Task<ActionResult<IEnumerable<MessageResponse>>> GetMessages(long id)
    {
        return Ok(await _chatService.GetMessagesAsync(id));
    }

    [HttpPost("{id}/messages")]
    public async Task<IActionResult> SaveMessage(long id, [FromBody] SaveMessageRequest request)
    {
        await _chatService.SaveMessageAsync(id, request);
        return Ok();
    }
}
