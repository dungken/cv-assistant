using CvAssistant.ApiGateway.Application.DTOs;
using CvAssistant.ApiGateway.Application.Interfaces.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api/templates")]
public class TemplateController : ControllerBase
{
    private readonly ICvTemplateService _templateService;

    public TemplateController(ICvTemplateService templateService)
    {
        _templateService = templateService;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<CvTemplateResponse>>> GetAll([FromQuery] bool includeUnpublished = false)
    {
        // Only admins can see unpublished templates
        if (includeUnpublished && !User.IsInRole("Admin"))
        {
             includeUnpublished = false;
        }
        
        var templates = await _templateService.GetAllAsync(includeUnpublished);
        return Ok(templates);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<CvTemplateResponse>> GetById(long id)
    {
        var template = await _templateService.GetByIdAsync(id);
        return Ok(template);
    }

    [HttpGet("category/{category}")]
    public async Task<ActionResult<IEnumerable<CvTemplateResponse>>> GetByCategory(string category)
    {
        var templates = await _templateService.GetByCategoryAsync(category);
        return Ok(templates);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<CvTemplateResponse>> Create(CreateCvTemplateRequest request)
    {
        var template = await _templateService.CreateAsync(request);
        return CreatedAtAction(nameof(GetById), new { id = template.Id }, template);
    }

    [HttpPut("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<CvTemplateResponse>> Update(long id, UpdateCvTemplateRequest request)
    {
        var template = await _templateService.UpdateAsync(id, request);
        return Ok(template);
    }

    [HttpDelete("{id}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(long id)
    {
        await _templateService.DeleteAsync(id);
        return NoContent();
    }
}
