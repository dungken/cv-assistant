using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using CvAssistant.ApiGateway.Application.Interfaces.Security;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace CvAssistant.ApiGateway.Infrastructure.Security;

public class JwtUtils : IJwtUtils
{
    private readonly string _secret;
    private readonly int _expirationMs;

    public JwtUtils(IConfiguration config)
    {
        // Defaults mimic the Java application.properties
        _secret = config["jwt:secret"] ?? "404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970";
        _expirationMs = int.TryParse(config["jwt:expiration"], out var exp) ? exp : 86400000;
    }

    public string GenerateToken(string email)
    {
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.ASCII.GetBytes(_secret);
        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(new[]
            {
                new Claim(ClaimTypes.NameIdentifier, email),
                new Claim(ClaimTypes.Email, email)
            }),
            Expires = DateTime.UtcNow.AddMilliseconds(_expirationMs),
            SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature)
        };
        
        var token = tokenHandler.CreateToken(tokenDescriptor);
        return tokenHandler.WriteToken(token);
    }
}
