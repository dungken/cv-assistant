using Microsoft.AspNetCore.Mvc;

namespace CvAssistant.ApiGateway.API.Controllers;

[ApiController]
[Route("api")]
public class HealthController : ControllerBase
{
    [HttpGet("health")]
    public ActionResult<object> Health()
    {
        return Ok(new
        {
            status = "UP",
            service = "api-gateway (dotnet 9 clean architecture)"
        });
    }
}
