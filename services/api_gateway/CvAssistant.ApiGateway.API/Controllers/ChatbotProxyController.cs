using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Application.DTOs;

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
    private readonly ICollectorService _collectorService;

    public ChatbotProxyController(IHttpClientFactory httpClientFactory, ILogger<ChatbotProxyController> logger, ICollectorService collectorService)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _collectorService = collectorService;
    }

    /// <summary>
    /// Send a message to the AI chatbot with streaming response.
    /// </summary>
    [HttpPost("chat/stream")]
    public async Task ChatStream([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        var request = new HttpRequestMessage(HttpMethod.Post, "/chat/stream") { Content = json };
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);
        
        Response.ContentType = "text/event-stream";
        Response.Headers["Cache-Control"] = "no-cache";
        Response.Headers["Connection"] = "keep-alive";

        await response.Content.CopyToAsync(Response.Body);
    }

    /// <summary>
    /// Generate a concise, context-aware title for a conversation.
    /// </summary>
    [HttpPost("chat/title")]
    public async Task<IActionResult> GenerateChatTitle([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/chat/title", json);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// Send a message to the specialized CV collector with streaming.
    /// </summary>
    [HttpPost("chat/collector/stream")]
    public async Task CollectorChatStream([FromBody] System.Text.Json.JsonElement body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            body.GetRawText(),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        var request = new HttpRequestMessage(HttpMethod.Post, "/chat/collector/stream") { Content = json };
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);

        Response.ContentType = "text/event-stream";
        
        // We need to capture the stream to extract metadata at the end for auto-saving
        using var responseStream = await response.Content.ReadAsStreamAsync();
        var buffer = new byte[8192];
        var fullResponseBuilder = new System.Text.StringBuilder();
        int bytesRead;

        while ((bytesRead = await responseStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
        {
            var chunk = System.Text.Encoding.UTF8.GetString(buffer, 0, bytesRead);
            fullResponseBuilder.Append(chunk);
            
            await Response.Body.WriteAsync(buffer, 0, bytesRead);
            await Response.Body.FlushAsync();
        }

        // After stream ends, try to extract metadata and save progress
        var fullContent = fullResponseBuilder.ToString();
        if (fullContent.Contains("[METADATA]"))
        {
            try
            {
                var metadataStr = fullContent.Split("[METADATA]")[1].Trim();
                var metadata = System.Text.Json.JsonSerializer.Deserialize<System.Text.Json.JsonElement>(metadataStr);
                
                if (body.TryGetProperty("session_id", out var sessionIdProp) && long.TryParse(sessionIdProp.GetString(), out long sessionId))
                {
                    var updateRequest = new UpdateCollectorProgressRequest
                    {
                        CurrentStep = metadata.GetProperty("step").GetInt32(),
                        DataJson = metadata.GetProperty("cv_data").GetRawText(),
                        IsComplete = metadata.GetProperty("step").GetInt32() >= 7
                    };
                    await _collectorService.UpdateProgressAsync(sessionId, updateRequest);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to auto-save collector progress after stream");
            }
        }
    }

    /// <summary>
    /// Send a message to the specialized CV collector (Sync).
    /// </summary>
    [HttpPost("chat/collector")]
    public async Task<IActionResult> CollectorChat([FromBody] System.Text.Json.JsonElement body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            body.GetRawText(),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying collector chatbot request");

        var response = await client.PostAsync("/chat/collector", json);
        var result = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            try 
            {
                // Parse response and save progress automatically
                var collectorResponse = System.Text.Json.JsonSerializer.Deserialize<System.Text.Json.JsonElement>(result);
                if (body.TryGetProperty("session_id", out var sessionIdProp) && long.TryParse(sessionIdProp.GetString(), out long sessionId))
                {
                    var updateRequest = new UpdateCollectorProgressRequest
                    {
                        CurrentStep = collectorResponse.GetProperty("current_step").GetInt32(),
                        DataJson = collectorResponse.GetProperty("cv_data").GetRawText(),
                        IsComplete = collectorResponse.GetProperty("current_step").GetInt32() >= 7
                    };
                    await _collectorService.UpdateProgressAsync(sessionId, updateRequest);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to auto-save collector progress in proxy");
            }
        }

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
    /// US-27: Get user memory profile.
    /// </summary>
    [HttpGet("memory/{userId}")]
    public async Task<IActionResult> GetMemory(string userId)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var response = await client.GetAsync($"/memory/{Uri.EscapeDataString(userId)}");
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// US-27: Update user memory fields.
    /// </summary>
    [HttpPut("memory/{userId}")]
    public async Task<IActionResult> UpdateMemory(string userId, [FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PutAsync($"/memory/{Uri.EscapeDataString(userId)}", json);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// US-27: Delete a specific memory field.
    /// </summary>
    [HttpDelete("memory/{userId}/{field}")]
    public async Task<IActionResult> DeleteMemoryField(string userId, string field)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var response = await client.DeleteAsync($"/memory/{Uri.EscapeDataString(userId)}/{Uri.EscapeDataString(field)}");
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// US-27: Delete all user memory.
    /// </summary>
    [HttpDelete("memory/{userId}")]
    public async Task<IActionResult> DeleteAllMemory(string userId)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var response = await client.DeleteAsync($"/memory/{Uri.EscapeDataString(userId)}");
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// US-17: Get explainable AI suggestions for CV improvement.
    /// </summary>
    [HttpPost("cv/optimize-suggestions")]
    public async Task<IActionResult> GetOptimizationSuggestions([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/cv/optimize-suggestions", json);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// AI Rewrite of bullet points into STAR format.
    /// </summary>
    [HttpPost("cv/rewrite")]
    public async Task<IActionResult> RewriteSection([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/cv/rewrite", json);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// Full CV optimization: section ordering + ATS analysis.
    /// </summary>
    [HttpPost("cv/generate")]
    public async Task<IActionResult> GenerateCv([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("ChatbotService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/cv/generate", json);
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
