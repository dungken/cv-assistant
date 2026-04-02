using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

/// <summary>
/// Proxies Skill service requests through the API Gateway with authentication.
/// </summary>
[ApiController]
[Route("api/skills")]
[Authorize]
public class SkillProxyController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<SkillProxyController> _logger;

    public SkillProxyController(IHttpClientFactory httpClientFactory, ILogger<SkillProxyController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Match CV skills against a job description with ontology-enhanced analysis.
    /// </summary>
    [HttpPost("match")]
    public async Task<IActionResult> Match([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying skill match request");

        var response = await client.PostAsync("/match", json);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Search jobs by keyword.
    /// </summary>
    [HttpGet("search")]
    public async Task<IActionResult> Search([FromQuery] string q)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync($"/search?q={Uri.EscapeDataString(q ?? "")}");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }
}
