using System.Net;
using System.Net.Mail;
using CvAssistant.ApiGateway.Application.Interfaces.Security;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace CvAssistant.ApiGateway.Infrastructure.Services;

public class EmailService : IEmailService
{
    private readonly IConfiguration _config;
    private readonly ILogger<EmailService> _logger;

    public EmailService(IConfiguration config, ILogger<EmailService> logger)
    {
        _config = config;
        _logger = logger;
    }

    public async Task SendEmailVerificationAsync(string toEmail, string token)
    {
        var subject = "CV Assistant - Xác thực email";
        var body = $@"
            <h2>Xác thực email của bạn</h2>
            <p>Cảm ơn bạn đã đăng ký. Mã xác thực của bạn là:</p>
            <h1 style='color: #6366f1; letter-spacing: 4px;'>{token}</h1>
            <p>Mã này có hiệu lực trong 24 giờ.</p>
        ";
        await SendAsync(toEmail, subject, body);
    }

    public async Task SendPasswordResetAsync(string toEmail, string otp)
    {
        var subject = "CV Assistant - Đặt lại mật khẩu";
        var body = $@"
            <h2>Đặt lại mật khẩu</h2>
            <p>Mã OTP để đặt lại mật khẩu của bạn:</p>
            <h1 style='color: #6366f1; letter-spacing: 4px;'>{otp}</h1>
            <p>Mã này có hiệu lực trong 15 phút.</p>
        ";
        await SendAsync(toEmail, subject, body);
    }

    private async Task SendAsync(string toEmail, string subject, string htmlBody)
    {
        var smtpHost = _config["Email:SmtpHost"] ?? "smtp.gmail.com";
        var smtpPort = int.TryParse(_config["Email:SmtpPort"], out var p) ? p : 587;
        var fromEmail = _config["Email:FromEmail"] ?? "noreply@cvassistant.com";
        var password = _config["Email:Password"] ?? "";

        if (string.IsNullOrEmpty(password))
        {
            _logger.LogWarning("Email service not configured. Token for {Email}: check server logs.", toEmail);
            _logger.LogInformation("Email to {ToEmail}: {Subject} - Body contains verification/reset code", toEmail, subject);
            return;
        }

        using var client = new SmtpClient(smtpHost, smtpPort)
        {
            Credentials = new NetworkCredential(fromEmail, password),
            EnableSsl = true
        };

        var message = new MailMessage(fromEmail, toEmail, subject, htmlBody)
        {
            IsBodyHtml = true
        };

        await client.SendMailAsync(message);
    }
}
