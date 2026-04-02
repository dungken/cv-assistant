using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

/// <summary>
/// Proxies Chatbot service requests through the API Gateway with authentication.
/// </summary>
[ApiController]
[Route("api/chatbot")]
[Authorize]
public class ChatbotProxyController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<ChatbotProxyController> _logger;

    public ChatbotProxyController(IHttpClientFactory httpClientFactory, ILogger<ChatbotProxyController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Send a message to the AI chatbot.
    /// </summary>
    [HttpPost("chat")]
    public async Task<IActionResult> Chat([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying chatbot request");

        var response = await client.PostAsync("/chat", json);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Get chatbot conversation history.
    /// </summary>
    [HttpGet("history/{sessionId}")]
    public async Task<IActionResult> History(string sessionId)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var response = await client.GetAsync($"/history/{Uri.EscapeDataString(sessionId)}");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Check chatbot service health.
    /// </summary>
    [HttpGet("health")]
    [AllowAnonymous]
    public async Task<IActionResult> Health()
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        try
        {
            var response = await client.GetAsync("/health");
            var result = await response.Content.ReadAsStringAsync();
            return Content(result, "application/json");
        }
        catch (Exception ex)
        {
            return Ok(new { status = "down", error = ex.Message });
        }
    }
}
