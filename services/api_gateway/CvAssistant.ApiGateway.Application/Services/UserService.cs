using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;

namespace CvAssistant.ApiGateway.Application.Services;

public class UserService : IUserService
{
    private readonly IUserRepository _userRepository;

    public UserService(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<UserProfileResponse> GetProfileAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        return new UserProfileResponse(user.Id, user.Email, user.Name ?? string.Empty, user.Bio ?? string.Empty);
    }

    public async Task<UserProfileResponse> UpdateProfileAsync(string email, UpdateUserRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email)
                   ?? throw new Exception("User not found");

        if (request.Name != null) user.Name = request.Name;
        if (request.Bio != null) user.Bio = request.Bio;

        await _userRepository.UpdateAsync(user);

        return new UserProfileResponse(user.Id, user.Email, user.Name ?? string.Empty, user.Bio ?? string.Empty);
    }
}
