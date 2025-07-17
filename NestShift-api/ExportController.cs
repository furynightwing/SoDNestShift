using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using sodoff.Model;

namespace sodoff.Controllers.Common;

[Route("ProfileWebService.asmx")]
[ApiController]
public class ExportController : ControllerBase
{
    private readonly DBContext ctx;

    public ExportController(DBContext ctx)
    {
        this.ctx = ctx;
    }

    [HttpPost]
    [Route("Export3")]
    public IActionResult Export([FromForm] string username, [FromForm] string password)
    {
        // Authenticate user by Username
        User? user = ctx.Users.FirstOrDefault(e => e.Username == username);

        if (user is null || new PasswordHasher<object>().VerifyHashedPassword(null, user.Password, password) == PasswordVerificationResult.Failed)
        {
            return Unauthorized("Invalid username or password.");
        }

        // Serialize to JSON
        var options = new JsonSerializerOptions
        {
            ReferenceHandler = ReferenceHandler.Preserve,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            WriteIndented = true
        };
        string jsonData = JsonSerializer.Serialize(user, options);

        return Ok(jsonData);
    }
}
