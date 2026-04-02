using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

/// <summary>
/// Proxies Career service requests through the API Gateway with authentication.
/// </summary>
[ApiController]
[Route("api/career")]
[Authorize]
public class CareerProxyController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<CareerProxyController> _logger;

    public CareerProxyController(IHttpClientFactory httpClientFactory, ILogger<CareerProxyController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Get career path recommendations based on current and target roles.
    /// </summary>
    [HttpPost("recommend")]
    public async Task<IActionResult> Recommend([FromBody] object body)
    {
        var client = _httpClientFactory.CreateClient("CareerService");
        var json = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(body),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        _logger.LogInformation("Proxying career recommendation request");

        var response = await client.PostAsync("/recommend", json);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// List or search available roles.
    /// </summary>
    [HttpGet("roles")]
    public async Task<IActionResult> Roles([FromQuery] string? q)
    {
        var client = _httpClientFactory.CreateClient("CareerService");
        var url = string.IsNullOrEmpty(q) ? "/roles" : $"/roles?q={Uri.EscapeDataString(q)}";
        var response = await client.GetAsync(url);
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }

    /// <summary>
    /// Get details for a specific role by O*NET code.
    /// </summary>
    [HttpGet("roles/{code}")]
    public async Task<IActionResult> RoleDetail(string code)
    {
        var client = _httpClientFactory.CreateClient("CareerService");
        var response = await client.GetAsync($"/roles/{Uri.EscapeDataString(code)}");
        var result = await response.Content.ReadAsStringAsync();

        return Content(result, "application/json");
    }
}
