using System.Net;
using System.Text.Json;

namespace CvAssistant.ApiGateway.API.Middleware;

public class ExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionMiddleware> _logger;

    public ExceptionMiddleware(RequestDelegate next, ILogger<ExceptionMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An unhandled exception occurred.");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        context.Response.ContentType = "application/json";
        
        // Use generic 400 Bad Request for business logic exceptions to match Java behavior,
        // or 500 Internal Server error for unexpected
        var statusCode = exception.Message switch
        {
            "User not found" => (int)HttpStatusCode.NotFound,
            "Email already exists" => (int)HttpStatusCode.Conflict,
            "Invalid credentials" => (int)HttpStatusCode.Unauthorized,
            _ => (int)HttpStatusCode.BadRequest
        };
        
        context.Response.StatusCode = statusCode;

        var response = new
        {
            error = exception.Message,
            status = statusCode
        };

        var json = JsonSerializer.Serialize(response);
        return context.Response.WriteAsync(json);
    }
}
