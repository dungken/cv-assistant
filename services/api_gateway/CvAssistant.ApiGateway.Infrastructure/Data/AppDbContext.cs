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
    public DbSet<CollectorProgress> CollectorProgresses { get; set; }
    public DbSet<JDHistory> JDHistories { get; set; }
    public DbSet<CvDocument> CvDocuments { get; set; }
    public DbSet<CvVersion> CvVersions { get; set; }
    public DbSet<CvTemplate> CvTemplates { get; set; }
    public DbSet<Feedback> Feedbacks { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Ensure email is unique across the Users table
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email)
            .IsUnique();

        // Filter out soft-deleted users by default
        modelBuilder.Entity<User>()
            .HasQueryFilter(u => !u.IsDeleted);

        // One-to-one relationship between ChatSession and CollectorProgress
        modelBuilder.Entity<ChatSession>()
            .HasOne(s => s.CollectorProgress)
            .WithOne(p => p.Session)
            .HasForeignKey<CollectorProgress>(p => p.SessionId);

        // CvDocument -> CvVersion (one-to-many)
        modelBuilder.Entity<CvDocument>()
            .HasMany(d => d.Versions)
            .WithOne(v => v.CvDocument)
            .HasForeignKey(v => v.CvDocumentId)
            .OnDelete(DeleteBehavior.Cascade);

        // CvDocument soft delete filter
        modelBuilder.Entity<CvDocument>()
            .HasQueryFilter(d => !d.IsDeleted);
    }
}
