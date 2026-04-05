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

    // ─── Knowledge Graph / Ontology Endpoints ─────────────────────────────────

    /// <summary>
    /// Get a single skill node with all relationships and metadata.
    /// </summary>
    [HttpGet("ontology/skill/{name}")]
    [AllowAnonymous]
    public async Task<IActionResult> GetSkillNode(string name)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        _logger.LogInformation("Proxying ontology skill lookup: {Name}", name);

        var response = await client.GetAsync($"/ontology/skill/{Uri.EscapeDataString(name)}");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Get graph data (nodes + edges) for visualization.
    /// </summary>
    [HttpGet("ontology/graph")]
    [AllowAnonymous]
    public async Task<IActionResult> GetGraphData(
        [FromQuery] string? center,
        [FromQuery] int depth = 1,
        [FromQuery] int max_nodes = 80)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = $"/ontology/graph?depth={depth}&max_nodes={max_nodes}";
        if (!string.IsNullOrWhiteSpace(center))
            qs += $"&center={Uri.EscapeDataString(center)}";

        _logger.LogInformation("Proxying ontology graph request: center={Center}", center ?? "(all)");

        var response = await client.GetAsync(qs);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Search skills by name (prefix/substring).
    /// </summary>
    [HttpGet("ontology/search")]
    [AllowAnonymous]
    public async Task<IActionResult> SearchSkills(
        [FromQuery] string q,
        [FromQuery] int limit = 20)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync($"/ontology/search?q={Uri.EscapeDataString(q ?? "")}&limit={limit}");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Get ontology statistics.
    /// </summary>
    [HttpGet("ontology/stats")]
    [AllowAnonymous]
    public async Task<IActionResult> GetOntologyStats()
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync("/ontology/stats");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// US-18: ATS Scoring.
    /// </summary>
    [HttpPost("cv/ats-score")]
    public async Task<IActionResult> GetAtsScore([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/cv/ats-score", json);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// US-19: Market analysis dashboard data.
    /// </summary>
    [HttpGet("market/overview")]
    [AllowAnonymous]
    public async Task<IActionResult> GetMarketOverview([FromQuery] string? industry)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = $"/market/overview";
        if (!string.IsNullOrWhiteSpace(industry))
            qs += $"?industry={Uri.EscapeDataString(industry)}";

        var response = await client.GetAsync(qs);
        var result = await response.Content.ReadAsStringAsync();
        return Content(result, "application/json");
    }

    /// <summary>
    /// List all skill categories.
    /// </summary>

    [HttpGet("ontology/categories")]
    [AllowAnonymous]
    public async Task<IActionResult> GetCategories()
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync("/ontology/categories");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }
}
