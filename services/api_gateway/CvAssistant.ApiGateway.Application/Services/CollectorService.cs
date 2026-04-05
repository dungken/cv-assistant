using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Repositories;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using CvAssistant.ApiGateway.Domain.Entities;

namespace CvAssistant.ApiGateway.Application.Services;

public class CollectorService : ICollectorService
{
    private readonly ICollectorRepository _collectorRepository;
    private readonly IChatSessionRepository _sessionRepository;

    public CollectorService(ICollectorRepository collectorRepository, IChatSessionRepository sessionRepository)
    {
        _collectorRepository = collectorRepository;
        _sessionRepository = sessionRepository;
    }

    public async Task<CollectorProgressResponse?> GetProgressAsync(long sessionId)
    {
        var progress = await _collectorRepository.GetBySessionIdAsync(sessionId);
        if (progress == null) return null;

        return new CollectorProgressResponse
        {
            Id = progress.Id,
            SessionId = progress.SessionId,
            CurrentStep = progress.CurrentStep,
            DataJson = progress.DataJson,
            IsComplete = progress.IsComplete,
            UpdatedAt = progress.UpdatedAt
        };
    }

    public async Task<CollectorProgressResponse> UpdateProgressAsync(long sessionId, UpdateCollectorProgressRequest request)
    {
        var session = await _sessionRepository.GetByIdAsync(sessionId) ?? throw new Exception("Session not found");
        var progress = await _collectorRepository.GetBySessionIdAsync(sessionId);

        if (progress == null)
        {
            progress = new CollectorProgress
            {
                SessionId = sessionId,
                CurrentStep = request.CurrentStep,
                DataJson = request.DataJson,
                IsComplete = request.IsComplete,
                UpdatedAt = DateTime.UtcNow
            };
            await _collectorRepository.AddAsync(progress);
        }
        else
        {
            progress.CurrentStep = request.CurrentStep;
            progress.DataJson = request.DataJson;
            progress.IsComplete = request.IsComplete;
            progress.UpdatedAt = DateTime.UtcNow;
            await _collectorRepository.UpdateAsync(progress);
        }

        // Update session timestamp too
        session.UpdatedAt = DateTime.UtcNow;
        await _sessionRepository.UpdateAsync(session);

        return new CollectorProgressResponse
        {
            Id = progress.Id,
            SessionId = progress.SessionId,
            CurrentStep = progress.CurrentStep,
            DataJson = progress.DataJson,
            IsComplete = progress.IsComplete,
            UpdatedAt = progress.UpdatedAt
        };
    }
}
