using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

/// <summary>
/// Proxies NER service requests through the API Gateway with authentication.
/// </summary>
[ApiController]
[Route("api/ner")]
[Authorize]
public class NerProxyController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<NerProxyController> _logger;

    public NerProxyController(IHttpClientFactory httpClientFactory, ILogger<NerProxyController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Parse a CV file (PDF/TXT/DOCX) and extract entities.
    /// </summary>
    [HttpPost("parse-cv")]
    [RequestSizeLimit(10_000_000)] // 10MB limit
    public async Task<IActionResult> ParseCv(IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest(new { error = "No file provided" });

        var client = _httpClientFactory.CreateClient("NerService");

        using var content = new MultipartFormDataContent();
        using var stream = file.OpenReadStream();
        var fileContent = new StreamContent(stream);
        fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(file.ContentType);
        content.Add(fileContent, "file", file.FileName);

        _logger.LogInformation("Proxying parse-cv request for file: {FileName}", file.FileName);

        var response = await client.PostAsync("/parse-cv", content);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Extract entities from plain text.
    /// </summary>
    [HttpPost("extract")]
    public async Task<IActionResult> Extract([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("NerService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        var response = await client.PostAsync("/extract", json);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Generate an ATS-compliant PDF from structured CV data.
    /// </summary>
    [HttpPost("generate-pdf")]
    public async Task<IActionResult> GeneratePdf([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("NerService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying PDF generation request");

        var response = await client.PostAsync("/generate-pdf", json);

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            return StatusCode((int)response.StatusCode, error);
        }

        var pdfStream = await response.Content.ReadAsStreamAsync();
        var contentDisposition = response.Content.Headers.ContentDisposition?.FileName ?? "cv.pdf";

        return File(pdfStream, "application/pdf", contentDisposition);
    }
}
