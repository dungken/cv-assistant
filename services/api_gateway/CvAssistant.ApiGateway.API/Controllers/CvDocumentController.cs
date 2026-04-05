using System.Security.Claims;
using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/cv-documents")]
[Authorize]
public class CvDocumentController : ControllerBase
{
    private readonly ICvDocumentService _service;

    public CvDocumentController(ICvDocumentService service)
    {
        _service = service;
    }

    private string GetEmail() => User.FindFirstValue(ClaimTypes.Email) ?? string.Empty;

    [HttpPost]
    public async Task<ActionResult<CvDocumentResponse>> Create(CreateCvDocumentRequest request)
    {
        var response = await _service.CreateAsync(GetEmail(), request);
        return Ok(response);
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<CvDocumentResponse>>> List([FromQuery] CvSearchRequest request)
    {
        var response = await _service.ListAsync(GetEmail(), request);
        return Ok(response);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<CvDocumentResponse>> GetById(long id)
    {
        var response = await _service.GetByIdAsync(GetEmail(), id);
        return Ok(response);
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<CvDocumentResponse>> Update(long id, UpdateCvDocumentRequest request)
    {
        var response = await _service.UpdateAsync(GetEmail(), id, request);
        return Ok(response);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(long id)
    {
        await _service.DeleteAsync(GetEmail(), id);
        return Ok(new { message = "CV document deleted" });
    }

    [HttpPost("{id}/restore")]
    public async Task<ActionResult<CvDocumentResponse>> Restore(long id)
    {
        var response = await _service.RestoreAsync(GetEmail(), id);
        return Ok(response);
    }

    // --- Version endpoints ---

    [HttpPost("{id}/versions")]
    public async Task<ActionResult<CvVersionDetailResponse>> CreateVersion(long id, CreateCvVersionRequest request)
    {
        var response = await _service.CreateVersionAsync(GetEmail(), id, request);
        return Ok(response);
    }

    [HttpGet("{id}/versions/{versionId}")]
    public async Task<ActionResult<CvVersionDetailResponse>> GetVersion(long id, long versionId)
    {
        var response = await _service.GetVersionAsync(id, versionId);
        return Ok(response);
    }

    [HttpPut("versions/{versionId}")]
    public async Task<IActionResult> UpdateVersion(long versionId, UpdateCvVersionRequest request)
    {
        await _service.UpdateVersionAsync(versionId, request);
        return Ok(new { message = "Version updated" });
    }

    [HttpGet("{id}/diff")]
    public async Task<ActionResult<CvDiffResponse>> Diff(long id, [FromQuery] int versionA, [FromQuery] int versionB)
    {
        var response = await _service.DiffAsync(id, versionA, versionB);
        return Ok(response);
    }

    [HttpPost("{id}/versions/{versionNumber}/restore")]
    public async Task<ActionResult<CvDocumentResponse>> RestoreVersion(long id, int versionNumber)
    {
        var response = await _service.RestoreVersionAsync(GetEmail(), id, versionNumber);
        return Ok(response);
    }
}
