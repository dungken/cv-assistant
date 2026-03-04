using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class CVHistoryService : ICVHistoryService
{
    private readonly ICVHistoryRepository _cvHistoryRepository;
    private readonly IUserRepository _userRepository;

    public CVHistoryService(ICVHistoryRepository cvHistoryRepository, IUserRepository userRepository)
    {
        _cvHistoryRepository = cvHistoryRepository;
        _userRepository = userRepository;
    }

    public async Task<IEnumerable<CVHistoryResponse>> GetHistoryAsync(string email)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");
        var histories = await _cvHistoryRepository.GetByUserIdOrderByUploadedDescAsync(user.Id);

        return histories.Select(h => new CVHistoryResponse(h.Id, h.FileName ?? string.Empty, h.FileUrl ?? string.Empty, h.UploadedAt));
    }

    public async Task<CVHistoryResponse> SaveHistoryAsync(string email, SaveCVHistoryRequest request)
    {
        var user = await _userRepository.GetByEmailAsync(email) ?? throw new Exception("User not found");
        
        var history = new CVHistory
        {
            UserId = user.Id,
            FileName = request.FileName,
            FileUrl = request.FileUrl,
            ExtractionResult = request.ExtractionResult,
            UploadedAt = DateTime.UtcNow
        };
        
        await _cvHistoryRepository.AddAsync(history);
        
        return new CVHistoryResponse(history.Id, history.FileName ?? string.Empty, history.FileUrl ?? string.Empty, history.UploadedAt);
    }
}
