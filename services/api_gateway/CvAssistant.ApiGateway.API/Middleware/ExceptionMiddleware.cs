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

        var statusCode = exception.Message switch
        {
            "User not found" => (int)HttpStatusCode.NotFound,
            "CV document not found" => (int)HttpStatusCode.NotFound,
            "Version not found" => (int)HttpStatusCode.NotFound,
            "Email already exists" => (int)HttpStatusCode.Conflict,
            "Invalid credentials" => (int)HttpStatusCode.Unauthorized,
            "Invalid refresh token" => (int)HttpStatusCode.Unauthorized,
            "Refresh token expired" => (int)HttpStatusCode.Unauthorized,
            "Invalid verification token" => (int)HttpStatusCode.BadRequest,
            "Verification token expired" => (int)HttpStatusCode.BadRequest,
            "Invalid OTP" => (int)HttpStatusCode.BadRequest,
            "OTP expired" => (int)HttpStatusCode.BadRequest,
            "Access denied" => (int)HttpStatusCode.Forbidden,
            "Recovery period expired" => (int)HttpStatusCode.Gone,
            _ when exception.Message.StartsWith("Version ") => (int)HttpStatusCode.NotFound,
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
