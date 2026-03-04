using CvAssistant.ApiGateway.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace CvAssistant.ApiGateway.Infrastructure.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<User> Users { get; set; }
    public DbSet<ChatSession> ChatSessions { get; set; }
    public DbSet<ChatMessage> ChatMessages { get; set; }
    public DbSet<CVHistory> CVHistories { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // Ensure email is unique across the Users table
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email)
            .IsUnique();

        // Foreign keys are mapped automatically by EF Core conventions based on Entity navigation properties,
        // but can be explicitly mapped here if needed.
    }
}
