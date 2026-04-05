using System.Collections.Concurrent;
using System.Net;

namespace CvAssistant.ApiGateway.API.Middleware;

public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private static readonly ConcurrentDictionary<string, RateLimitEntry> _clients = new();
    private const int MaxAttempts = 5;
    private static readonly TimeSpan Window = TimeSpan.FromMinutes(1);

    public RateLimitingMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var path = context.Request.Path.Value?.ToLower() ?? "";
        if (!path.Contains("/api/auth/login") && !path.Contains("/api/auth/reset-password"))
        {
            await _next(context);
            return;
        }

        var clientIp = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
        var key = $"{clientIp}:{path}";

        var entry = _clients.GetOrAdd(key, _ => new RateLimitEntry());

        lock (entry)
        {
            entry.CleanExpired();

            if (entry.Attempts.Count >= MaxAttempts)
            {
                context.Response.StatusCode = (int)HttpStatusCode.TooManyRequests;
                context.Response.ContentType = "application/json";
                context.Response.WriteAsync("{\"error\":\"Too many attempts. Please try again later.\",\"status\":429}");
                return;
            }

            entry.Attempts.Add(DateTime.UtcNow);
        }

        await _next(context);
    }

    private class RateLimitEntry
    {
        public List<DateTime> Attempts { get; } = new();

        public void CleanExpired()
        {
            var cutoff = DateTime.UtcNow - Window;
            Attempts.RemoveAll(t => t < cutoff);
        }
    }
}
