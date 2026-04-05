using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class JDHistoryService : IJDHistoryService
{
    private readonly IJDHistoryRepository _jdHistoryRepository;
    private readonly IUserRepository _userRepository;

    public JDHistoryService(IJDHistoryRepository jdHistoryRepository, IUserRepository userRepository)
    {
        _jdHistoryRepository = jdHistoryRepository;
        _userRepository = userRepository;
    }

    public async Task<IEnumerable<JDHistoryResponse>> GetHistoryAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");
        var histories = await _jdHistoryRepository.GetByUserIdOrderByCreatedDescAsync(user.Id);

        return histories.Select(h => new JDHistoryResponse(
            h.Id,
            h.Title ?? string.Empty,
            h.Company ?? string.Empty,
            h.InputMethod ?? "text",
            h.CreatedAt
        ));
    }

    public async Task<JDHistoryResponse> SaveHistoryAsync(string email, SaveJDHistoryRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");

        var history = new JDHistory
        {
            UserId = user.Id,
            Title = request.Title,
            Company = request.Company,
            FileName = request.FileName,
            FileUrl = request.FileUrl,
            SourceUrl = request.SourceUrl,
            InputMethod = request.InputMethod,
            ExtractionResult = request.ExtractionResult,
            CreatedAt = DateTime.UtcNow
        };

        await _jdHistoryRepository.AddAsync(history);

        return new JDHistoryResponse(
            history.Id,
            history.Title ?? string.Empty,
            history.Company ?? string.Empty,
            history.InputMethod ?? "text",
            history.CreatedAt
        );
    }

    public async Task DeleteHistoryAsync(long id)
    {
        await _jdHistoryRepository.DeleteAsync(id);
    }
}
