using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using System.Text.Json;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Application.DTOs;

namespace CvAssistant.ApiGateway.API.Controllers;

/// <summary>
/// Proxies JD (Job Description) parsing requests through the API Gateway.
/// Routes to NER service for parsing, saves results to JDHistory.
/// </summary>
[ApiController]
[Route("api/jd")]
[Authorize]
public class JDProxyController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<JDProxyController> _logger;
    private readonly IJDHistoryService _jdHistoryService;
    private readonly IWebHostEnvironment _environment;

    public JDProxyController(
        IHttpClientFactory httpClientFactory,
        ILogger<JDProxyController> logger,
        IJDHistoryService jdHistoryService,
        IWebHostEnvironment environment)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _jdHistoryService = jdHistoryService;
        _environment = environment;
    }

    /// <summary>
    /// Parse a JD file (PDF/DOCX/TXT) and extract structured information.
    /// </summary>
    [HttpPost("parse-file")]
    [RequestSizeLimit(10_000_000)]
    public async Task<IActionResult> ParseJDFile(IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest(new { error = "No file provided" });

        var client = _httpClientFactory.CreateClient("NerService");

        using var content = new MultipartFormDataContent();
        using var stream = file.OpenReadStream();
        var fileContent = new StreamContent(stream);
        fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(file.ContentType);
        content.Add(fileContent, "file", file.FileName);

        _logger.LogInformation("Proxying parse-jd request for file: {FileName}", file.FileName);

        var response = await client.PostAsync("/parse-jd", content);
        var result = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            await SaveJDHistory(result, file.FileName, null, "file");
        }

        return Content(result, "application/json");
    }

    /// <summary>
    /// Parse JD from pasted text.
    /// </summary>
    [HttpPost("parse-text")]
    public async Task<IActionResult> ParseJDText([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("NerService");
        var json = new StringContent(
            JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying parse-jd-text request");

        var response = await client.PostAsync("/parse-jd-text", json);
        var result = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            await SaveJDHistory(result, null, null, "text");
        }

        return Content(result, "application/json");
    }

    /// <summary>
    /// Parse JD from a URL.
    /// </summary>
    [HttpPost("parse-url")]
    public async Task<IActionResult> ParseJDUrl([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("NerService");
        var json = new StringContent(
            JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying parse-jd-url request");

        var response = await client.PostAsync("/parse-jd-url", json);
        var result = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            // Extract URL from request body
            string? sourceUrl = null;
            try
            {
                using var doc = JsonDocument.Parse(JsonSerializer.Serialize(body));
                sourceUrl = doc.RootElement.GetProperty("url").GetString();
            }
            catch { }

            await SaveJDHistory(result, null, sourceUrl, "url");
        }

        return Content(result, "application/json");
    }

    /// <summary>
    /// Get JD history for the current user.
    /// </summary>
    [HttpGet("history")]
    public async Task<IActionResult> GetHistory()
    {
        var email = User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;
        if (string.IsNullOrEmpty(email))
            return Unauthorized();

        var history = await _jdHistoryService.GetHistoryAsync(email);
        return Ok(history);
    }

    /// <summary>
    /// Delete a JD history entry.
    /// </summary>
    [HttpDelete("history/{id}")]
    public async Task<IActionResult> DeleteHistory(long id)
    {
        await _jdHistoryService.DeleteHistoryAsync(id);
        return NoContent();
    }

    private async Task SaveJDHistory(string result, string? fileName, string? sourceUrl, string inputMethod)
    {
        try
        {
            var email = User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;
            if (string.IsNullOrEmpty(email)) return;

            // Extract title and company from the result
            string? title = null;
            string? company = null;
            try
            {
                using var doc = JsonDocument.Parse(result);
                title = doc.RootElement.TryGetProperty("title", out var t) ? t.GetString() : null;
                company = doc.RootElement.TryGetProperty("company", out var c) ? c.GetString() : null;
            }
            catch { }

            await _jdHistoryService.SaveHistoryAsync(email, new SaveJDHistoryRequest(
                title, company, fileName, null, sourceUrl, inputMethod, result
            ));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving JD history to database");
        }
    }
}
