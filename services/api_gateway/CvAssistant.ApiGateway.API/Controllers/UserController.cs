using System.Security.Claims;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/user")]
[Authorize]
public class UserController : ControllerBase
{
    private readonly IUserService _userService;

    public UserController(IUserService userService)
    {
        _userService = userService;
    }

    private string GetEmail() => User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;

    [HttpGet("profile")]
    public async Task<ActionResult<UserProfileResponse>> GetProfile()
    {
        var response = await _userService.GetProfileAsync(GetEmail());
        return Ok(response);
    }

    [HttpPut("profile")]
    public async Task<ActionResult<UserProfileResponse>> UpdateProfile(UpdateUserRequest request)
    {
        var response = await _userService.UpdateProfileAsync(GetEmail(), request);
        return Ok(response);
    }
}
