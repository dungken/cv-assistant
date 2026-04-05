using System.Diagnostics;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/admin/monitoring")]
[Authorize(Roles = "Admin")]
public class MonitoringController : ControllerBase
{
    private readonly IWebHostEnvironment _env;

    public MonitoringController(IWebHostEnvironment env)
    {
        _env = env;
    }

    [HttpGet("stats")]
    public IActionResult GetStats()
    {
        var process = Process.GetCurrentProcess();
        var stats = new
        {
            cpuUsage = "N/A", // Basic implementation doesn't track CPU % easily without more complex logic
            memoryUsage = $"{process.WorkingSet64 / 1024 / 1024} MB",
            uptime = (DateTime.Now - process.StartTime).ToString(@"dd\.hh\:mm\:ss"),
            threadCount = process.Threads.Count,
            os = Environment.OSVersion.ToString(),
            dotnetVersion = Environment.Version.ToString(),
            status = "Healthy"
        };

        return Ok(stats);
    }

    [HttpGet("logs")]
    public async Task<IActionResult> GetLogs([FromQuery] int tail = 100)
    {
        // Look for log files in current directory or appsettings configured path
        // Assuming logs are in "logs" folder in content root
        var logPath = Path.Combine(_env.ContentRootPath, "logs");
        if (!Directory.Exists(logPath))
        {
            return Ok(new { message = "Log directory not found", logs = new List<string>() });
        }

        var logFiles = Directory.GetFiles(logPath, "*.log");
        if (logFiles.Length == 0)
        {
             return Ok(new { message = "No log files found", logs = new List<string>() });
        }

        var latestLog = logFiles.OrderByDescending(f => f).First();
        var lines = await System.IO.File.ReadAllLinesAsync(latestLog);
        var recentLogs = lines.Reverse().Take(tail).ToList();

        return Ok(new { fileName = Path.GetFileName(latestLog), logs = recentLogs });
    }
    
    [HttpGet("health")]
    [AllowAnonymous] // Allow public health check
    public IActionResult Health()
    {
        return Ok(new { status = "Healthy", timestamp = DateTime.UtcNow });
    }
}
