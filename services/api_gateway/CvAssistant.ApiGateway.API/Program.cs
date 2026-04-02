using System.Text;
using CvAssistant.ApiGateway.API.Middleware;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Security;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Application.Services;
using CvAssistant.ApiGateway.Infrastructure.Data;
using CvAssistant.ApiGateway.Infrastructure.Repositories;
using CvAssistant.ApiGateway.Infrastructure.Security;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

// 1. DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// 2. Repositories
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IChatSessionRepository, ChatSessionRepository>();
builder.Services.AddScoped<IChatMessageRepository, ChatMessageRepository>();
builder.Services.AddScoped<ICVHistoryRepository, CVHistoryRepository>();

// 3. Security
builder.Services.AddSingleton<IJwtUtils, JwtUtils>();
builder.Services.AddSingleton<IPasswordHasher, PasswordHasher>();

// 4. Services
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<ICVHistoryService, CVHistoryService>();

// 5. HttpClient for proxying to Python microservices
builder.Services.AddHttpClient("NerService", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Services:NerUrl"] ?? "http://localhost:5001");
    client.Timeout = TimeSpan.FromSeconds(60);
});
builder.Services.AddHttpClient("SkillService", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Services:SkillUrl"] ?? "http://localhost:5002");
    client.Timeout = TimeSpan.FromSeconds(30);
});
builder.Services.AddHttpClient("CareerService", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Services:CareerUrl"] ?? "http://localhost:5003");
    client.Timeout = TimeSpan.FromSeconds(30);
});
builder.Services.AddHttpClient("ChatbotService", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Services:ChatbotUrl"] ?? "http://localhost:5004");
    client.Timeout = TimeSpan.FromSeconds(120);
});

builder.Services.AddControllers();

// 5. JWT Authentication
var secretKey = builder.Configuration["jwt:secret"] ?? "404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970";
var key = Encoding.ASCII.GetBytes(secretKey);

builder.Services.AddAuthentication(x =>
{
    x.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    x.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(x =>
{
    x.RequireHttpsMetadata = false;
    x.SaveToken = true;
    x.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(key),
        ValidateIssuer = false,
        ValidateAudience = false,
        ValidateLifetime = true,
        ClockSkew = TimeSpan.Zero
    };
});

// 6. CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll",
        builder =>
        {
            builder.AllowAnyOrigin()
                   .AllowAnyMethod()
                   .AllowAnyHeader();
        });
});

// 7. Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "CvAssistant.ApiGateway", Version = "v1" });
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\"",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

app.UseMiddleware<ExceptionMiddleware>();

app.UseCors("AllowAll");

app.Urls.Add("http://0.0.0.0:8081");

app.MapGet("/swagger-ui.html", () => Results.Redirect("/swagger/index.html"));

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
