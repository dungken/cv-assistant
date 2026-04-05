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

    [HttpPost("avatar")]
    public async Task<ActionResult<UserProfileResponse>> UploadAvatar(IFormFile file)
    {
        if (file.Length == 0 || file.Length > 5 * 1024 * 1024)
            return BadRequest(new { error = "File must be between 1 byte and 5MB" });

        var allowedTypes = new[] { "image/jpeg", "image/png", "image/webp" };
        if (!allowedTypes.Contains(file.ContentType))
            return BadRequest(new { error = "Only JPEG, PNG, and WebP images are allowed" });

        using var stream = file.OpenReadStream();
        var response = await _userService.UploadAvatarAsync(GetEmail(), stream, file.FileName);
        return Ok(response);
    }

    [HttpPut("change-password")]
    public async Task<IActionResult> ChangePassword(ChangePasswordRequest request)
    {
        await _userService.ChangePasswordAsync(GetEmail(), request);
        return Ok(new { message = "Password changed successfully" });
    }

    [HttpDelete("account")]
    public async Task<IActionResult> DeleteAccount(DeleteAccountRequest request)
    {
        await _userService.DeleteAccountAsync(GetEmail(), request);
        return Ok(new { message = "Account deleted successfully" });
    }
}
