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
    /// Forward an HttpResponseMessage to the client, preserving status code so
    /// the browser sees real 404/422/500 instead of 200-with-error-body.
    /// </summary>
    private async Task<IActionResult> ForwardAsync(HttpResponseMessage upstream)
    {
        var body = await upstream.Content.ReadAsStringAsync();
        var contentType = upstream.Content.Headers.ContentType?.ToString() ?? "application/json";
        return new ContentResult
        {
            StatusCode = (int)upstream.StatusCode,
            ContentType = contentType,
            Content = body,
        };
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
    /// Market Intelligence dashboard — KPIs + 8 chart datasets in one call.
    /// </summary>
    [HttpGet("market-intel/dashboard")]
    [AllowAnonymous]
    public async Task<IActionResult> GetMarketIntelDashboard(
        [FromQuery] string? source,
        [FromQuery] string? role_group,
        [FromQuery] string? seniority)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = new List<string>();
        if (!string.IsNullOrWhiteSpace(source)) qs.Add($"source={Uri.EscapeDataString(source)}");
        if (!string.IsNullOrWhiteSpace(role_group)) qs.Add($"role_group={Uri.EscapeDataString(role_group)}");
        if (!string.IsNullOrWhiteSpace(seniority)) qs.Add($"seniority={Uri.EscapeDataString(seniority)}");
        var url = "/market-intel/dashboard" + (qs.Count > 0 ? "?" + string.Join("&", qs) : "");

        var response = await client.GetAsync(url);
        var result = await response.Content.ReadAsStringAsync();
        return new ContentResult { Content = result, ContentType = "application/json", StatusCode = (int)response.StatusCode };
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

    // ─── Tuần 10: standalone Freshness compute (no user_id, stateless) ────────

    /// <summary>
    /// Compute Freshness Score from skills + role without persisting.
    /// </summary>
    [HttpPost("cv/freshness")]
    public async Task<IActionResult> ComputeFreshness([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/cv/freshness", json);
        return await ForwardAsync(response);
    }

    // ─── Tuần 12: stateless Learning Path (client supplies JD list) ───────────

    /// <summary>
    /// Run Learning Path Optimizer with caller-supplied JDs (no CV state read).
    /// </summary>
    [HttpPost("learning-path")]
    public async Task<IActionResult> LearningPath([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/learning-path", json);
        return await ForwardAsync(response);
    }

    // ─── Tuần 14: user-scoped CV Health Intelligence endpoints ────────────────

    /// <summary>
    /// Upsert the user's stored CV. Triggers a BackgroundTask Freshness recompute.
    /// </summary>
    [HttpPost("cv/me")]
    public async Task<IActionResult> UpsertCv([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        _logger.LogInformation("Proxying CV upsert");
        var response = await client.PostAsync("/cv/me", json);
        return await ForwardAsync(response);
    }

    /// <summary>
    /// Get the user's saved CV config (target_role, seniority, years, location, work_modes)
    /// to prefill the dashboard form on reload. 404 nếu chưa từng upsert.
    /// </summary>
    [HttpGet("cv/me")]
    public async Task<IActionResult> GetSavedCv([FromQuery] string user_id)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync($"/cv/me?user_id={Uri.EscapeDataString(user_id ?? "")}");
        return await ForwardAsync(response);
    }


    /// <summary>
    /// Current Multi-criteria Freshness Score (8 dim) for `user_id`.
    /// </summary>
    [HttpGet("health-score")]
    public async Task<IActionResult> GetHealthScore([FromQuery] string user_id)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = $"/health-score?user_id={Uri.EscapeDataString(user_id ?? "")}";
        var response = await client.GetAsync(qs);
        return await ForwardAsync(response);
    }

    /// <summary>
    /// JDs posted recently that match the user's stored CV well.
    /// </summary>
    [HttpGet("opportunity-window")]
    public async Task<IActionResult> GetOpportunityWindow(
        [FromQuery] string user_id,
        [FromQuery] int days = 30,
        [FromQuery] int limit = 20,
        [FromQuery] double min_match = 0.4,
        [FromQuery] string? sort = "match",
        [FromQuery(Name = "work_modes")] List<string>? workModes = null)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = $"/opportunity-window?user_id={Uri.EscapeDataString(user_id ?? "")}" +
                 $"&days={days}&limit={limit}&min_match={min_match.ToString(System.Globalization.CultureInfo.InvariantCulture)}" +
                 $"&sort={Uri.EscapeDataString(sort ?? "match")}";
        if (workModes != null)
            foreach (var m in workModes)
                qs += $"&work_modes={Uri.EscapeDataString(m)}";
        var response = await client.GetAsync(qs);
        return await ForwardAsync(response);
    }

    /// <summary>
    /// Update per-user JD application status (saved/applied/interview/rejected/new).
    /// </summary>
    [HttpPut("jd-status")]
    public async Task<IActionResult> UpsertJdStatus(
        [FromQuery] string user_id,
        [FromQuery] string jd_key,
        [FromQuery] string status)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var qs = $"/jd-status?user_id={Uri.EscapeDataString(user_id ?? "")}" +
                 $"&jd_key={Uri.EscapeDataString(jd_key ?? "")}" +
                 $"&status={Uri.EscapeDataString(status ?? "")}";
        var response = await client.PutAsync(qs, new StringContent(""));
        return await ForwardAsync(response);
    }

    /// <summary>
    /// Counts of JDs per status — used for status filter tabs in OpportunityWindow.
    /// </summary>
    [HttpGet("jd-status/stats")]
    public async Task<IActionResult> GetJdStatusStats([FromQuery] string user_id)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var response = await client.GetAsync($"/jd-status/stats?user_id={Uri.EscapeDataString(user_id ?? "")}");
        return await ForwardAsync(response);
    }

    /// <summary>
    /// User-friendly Learning Path: builds JD target set from stored CV + market data.
    /// </summary>
    [HttpPost("learning-path/me")]
    public async Task<IActionResult> LearningPathMe([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("SkillService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );
        var response = await client.PostAsync("/learning-path/me", json);
        return await ForwardAsync(response);
    }
}
