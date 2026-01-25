# 23. Security Specification - Đặc Tả Bảo Mật

> **Document Version**: 1.0
> **Last Updated**: 2026-01-24
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [17_api_specifications.md](./17_api_specifications.md)

---

## 1. Security Overview

### 1.1 Security Objectives

```
Security Goals:
├── Confidentiality
│   ├── Protect user CV data
│   ├── Secure authentication tokens
│   └── Encrypt sensitive data in transit
│
├── Integrity
│   ├── Prevent unauthorized data modification
│   ├── Validate input data
│   └── Ensure data consistency
│
└── Availability
    ├── Rate limiting to prevent DoS
    ├── Service health monitoring
    └── Graceful degradation
```

### 1.2 Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Unauthorized access to CVs | High | Medium | JWT authentication, role-based access |
| SQL/NoSQL injection | High | Low | Parameterized queries, input validation |
| XSS attacks | Medium | Medium | Output encoding, CSP headers |
| Token theft | High | Low | Secure storage, token expiration |
| Data breach | Critical | Low | Encryption, access logging |
| DoS attacks | Medium | Medium | Rate limiting, request throttling |

---

## 2. Authentication

### 2.1 JWT Authentication Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │     │  API Gateway │     │   Database   │
│   (React)    │     │(Spring Boot) │     │ (PostgreSQL) │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ POST /auth/login   │                    │
       │ {email, password}  │                    │
       │───────────────────▶│                    │
       │                    │ Verify credentials │
       │                    │───────────────────▶│
       │                    │◀───────────────────│
       │                    │                    │
       │                    │ Generate JWT       │
       │                    │ (access + refresh) │
       │                    │                    │
       │◀───────────────────│                    │
       │ {access_token,     │                    │
       │  refresh_token}    │                    │
       │                    │                    │
       │ API Request        │                    │
       │ Authorization:     │                    │
       │ Bearer <token>     │                    │
       │───────────────────▶│                    │
       │                    │ Validate JWT       │
       │                    │ Extract user_id    │
       │                    │                    │
```

### 2.2 JWT Configuration

```java
// Spring Boot JWT Configuration
@Configuration
public class JwtConfig {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpiration = 3600000; // 1 hour

    @Value("${jwt.refresh-expiration}")
    private long refreshExpiration = 604800000; // 7 days

    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", userDetails.getAuthorities());

        return Jwts.builder()
            .setClaims(claims)
            .setSubject(userDetails.getUsername())
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + jwtExpiration))
            .signWith(SignatureAlgorithm.HS512, jwtSecret)
            .compact();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
}
```

### 2.3 Token Storage

```typescript
// Frontend token storage (secure)
class TokenStorage {
  private static ACCESS_TOKEN_KEY = 'cv_assistant_access_token';
  private static REFRESH_TOKEN_KEY = 'cv_assistant_refresh_token';

  // Store tokens securely
  static setTokens(accessToken: string, refreshToken: string): void {
    // Use httpOnly cookies for production
    // For development, use sessionStorage (not localStorage)
    sessionStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    sessionStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  static getAccessToken(): string | null {
    return sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static clearTokens(): void {
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }
}
```

---

## 3. Authorization

### 3.1 Role-Based Access Control (RBAC)

```yaml
Roles:
  USER:
    description: "Regular user"
    permissions:
      - "chat:create"
      - "chat:read:own"
      - "cv:upload:own"
      - "cv:read:own"
      - "thread:create"
      - "thread:read:own"
      - "thread:delete:own"

  ADMIN:
    description: "Administrator"
    permissions:
      - "chat:*"
      - "cv:*"
      - "thread:*"
      - "user:*"
      - "system:*"
```

### 3.2 Spring Security Configuration

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable() // Disable for API
            .cors().and()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeHttpRequests()
                // Public endpoints
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/health").permitAll()
                // Protected endpoints
                .requestMatchers("/api/chat/**").authenticated()
                .requestMatchers("/api/cv/**").authenticated()
                .requestMatchers("/api/threads/**").authenticated()
                // Admin endpoints
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
```

### 3.3 Resource-Level Authorization

```java
@Service
public class CVAuthorizationService {

    public boolean canAccessCV(String userId, String cvId) {
        CV cv = cvRepository.findById(cvId)
            .orElseThrow(() -> new ResourceNotFoundException("CV not found"));

        // User can only access their own CVs
        return cv.getUserId().equals(userId);
    }

    public boolean canAccessThread(String userId, String threadId) {
        Thread thread = threadRepository.findById(threadId)
            .orElseThrow(() -> new ResourceNotFoundException("Thread not found"));

        return thread.getUserId().equals(userId);
    }
}

// Usage in Controller
@GetMapping("/cv/{cvId}")
@PreAuthorize("@cvAuthorizationService.canAccessCV(principal.id, #cvId)")
public ResponseEntity<CVResponse> getCV(@PathVariable String cvId) {
    // ...
}
```

---

## 4. Data Protection

### 4.1 Data Classification

| Data Type | Classification | Protection Level |
|-----------|---------------|------------------|
| User credentials | Critical | Encrypted, hashed |
| CV content | Confidential | Encrypted in transit |
| Chat history | Confidential | Per-user access only |
| Extracted entities | Confidential | Per-user access only |
| Knowledge base | Internal | Read-only access |
| System logs | Internal | Admin access only |

### 4.2 Password Security

```java
@Service
public class PasswordService {

    private final BCryptPasswordEncoder passwordEncoder;

    public PasswordService() {
        // BCrypt with strength 12 (2^12 rounds)
        this.passwordEncoder = new BCryptPasswordEncoder(12);
    }

    public String hashPassword(String rawPassword) {
        // Validate password strength
        validatePasswordStrength(rawPassword);
        return passwordEncoder.encode(rawPassword);
    }

    public boolean verifyPassword(String rawPassword, String hashedPassword) {
        return passwordEncoder.matches(rawPassword, hashedPassword);
    }

    private void validatePasswordStrength(String password) {
        if (password.length() < 8) {
            throw new WeakPasswordException("Password must be at least 8 characters");
        }
        if (!password.matches(".*[A-Z].*")) {
            throw new WeakPasswordException("Password must contain uppercase letter");
        }
        if (!password.matches(".*[a-z].*")) {
            throw new WeakPasswordException("Password must contain lowercase letter");
        }
        if (!password.matches(".*\\d.*")) {
            throw new WeakPasswordException("Password must contain digit");
        }
    }
}
```

### 4.3 Data Encryption

```yaml
Encryption Configuration:
  in_transit:
    protocol: TLS 1.3
    certificates: Let's Encrypt (production)
    self_signed: Development only

  at_rest:
    database: PostgreSQL native encryption (optional)
    files: AES-256 for uploaded CVs (optional)
    keys: Environment variables / Secrets manager
```

---

## 5. Input Validation

### 5.1 API Input Validation

```java
// Request DTOs with validation
@Data
public class RegisterRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 255, message = "Email too long")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 100, message = "Password must be 8-100 characters")
    private String password;

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be 2-100 characters")
    @Pattern(regexp = "^[a-zA-Z\\s]+$", message = "Name can only contain letters")
    private String name;
}

@Data
public class ChatRequest {

    @NotBlank(message = "Message is required")
    @Size(max = 10000, message = "Message too long")
    private String message;

    @Size(max = 36, message = "Invalid thread ID")
    @Pattern(regexp = "^[a-f0-9-]+$", message = "Invalid thread ID format")
    private String threadId;
}
```

### 5.2 File Upload Validation

```java
@Service
public class FileValidationService {

    private static final List<String> ALLOWED_TYPES = List.of(
        "application/pdf"
    );

    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

    public void validateFile(MultipartFile file) {
        // Check file size
        if (file.getSize() > MAX_FILE_SIZE) {
            throw new InvalidFileException("File size exceeds 10MB limit");
        }

        // Check content type
        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_TYPES.contains(contentType)) {
            throw new InvalidFileException("Only PDF files are allowed");
        }

        // Check file extension
        String filename = file.getOriginalFilename();
        if (filename == null || !filename.toLowerCase().endsWith(".pdf")) {
            throw new InvalidFileException("Invalid file extension");
        }

        // Validate PDF magic bytes
        try {
            byte[] header = new byte[4];
            file.getInputStream().read(header);
            if (header[0] != 0x25 || header[1] != 0x50 ||
                header[2] != 0x44 || header[3] != 0x46) {
                throw new InvalidFileException("Invalid PDF file");
            }
        } catch (IOException e) {
            throw new InvalidFileException("Cannot read file");
        }
    }
}
```

### 5.3 SQL Injection Prevention

```java
// Use parameterized queries (Spring Data JPA)
@Repository
public interface UserRepository extends JpaRepository<User, String> {

    // Safe: Spring Data JPA handles parameterization
    Optional<User> findByEmail(String email);

    // Safe: Named parameters
    @Query("SELECT u FROM User u WHERE u.email = :email AND u.active = true")
    Optional<User> findActiveByEmail(@Param("email") String email);

    // NEVER do this:
    // @Query("SELECT u FROM User u WHERE u.email = '" + email + "'")
}
```

---

## 6. Rate Limiting

### 6.1 Rate Limit Configuration

```java
@Configuration
public class RateLimitConfig {

    @Bean
    public RateLimiter authRateLimiter() {
        return RateLimiter.of("auth",
            RateLimiterConfig.custom()
                .limitForPeriod(5)           // 5 attempts
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ZERO)
                .build());
    }

    @Bean
    public RateLimiter chatRateLimiter() {
        return RateLimiter.of("chat",
            RateLimiterConfig.custom()
                .limitForPeriod(30)          // 30 messages
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ZERO)
                .build());
    }

    @Bean
    public RateLimiter uploadRateLimiter() {
        return RateLimiter.of("upload",
            RateLimiterConfig.custom()
                .limitForPeriod(10)          // 10 uploads
                .limitRefreshPeriod(Duration.ofHours(1))
                .timeoutDuration(Duration.ZERO)
                .build());
    }
}
```

### 6.2 Rate Limit Matrix

| Endpoint | Limit | Period | Scope |
|----------|-------|--------|-------|
| `/api/auth/login` | 5 | 1 minute | Per IP |
| `/api/auth/register` | 3 | 1 hour | Per IP |
| `/api/chat` | 30 | 1 minute | Per user |
| `/api/upload` | 10 | 1 hour | Per user |
| `/api/*` (general) | 100 | 1 minute | Per user |

---

## 7. Logging & Monitoring

### 7.1 Security Logging

```java
@Aspect
@Component
public class SecurityAuditAspect {

    private static final Logger auditLogger =
        LoggerFactory.getLogger("SECURITY_AUDIT");

    @Around("@annotation(AuditLog)")
    public Object logSecurityEvent(ProceedingJoinPoint joinPoint) throws Throwable {
        String userId = getCurrentUserId();
        String action = joinPoint.getSignature().getName();

        try {
            Object result = joinPoint.proceed();

            auditLogger.info("AUDIT: user={} action={} status=SUCCESS",
                userId, action);

            return result;
        } catch (Exception e) {
            auditLogger.warn("AUDIT: user={} action={} status=FAILED error={}",
                userId, action, e.getMessage());
            throw e;
        }
    }
}

// Usage
@AuditLog
@PostMapping("/cv/upload")
public ResponseEntity<?> uploadCV(...) { ... }
```

### 7.2 Sensitive Data Masking

```java
public class DataMasker {

    public static String maskEmail(String email) {
        if (email == null || !email.contains("@")) return "***";
        String[] parts = email.split("@");
        return parts[0].charAt(0) + "***@" + parts[1];
    }

    public static String maskToken(String token) {
        if (token == null || token.length() < 10) return "***";
        return token.substring(0, 5) + "..." + token.substring(token.length() - 5);
    }
}

// In logs: "User j***@gmail.com logged in with token eyJhb...xyz12"
```

---

## 8. CORS Configuration

```java
@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();

        // Allowed origins (restrict in production)
        config.setAllowedOrigins(List.of(
            "http://localhost:3000",  // Development
            "https://cv-assistant.example.com"  // Production
        ));

        // Allowed methods
        config.setAllowedMethods(List.of(
            "GET", "POST", "PUT", "DELETE", "OPTIONS"
        ));

        // Allowed headers
        config.setAllowedHeaders(List.of(
            "Authorization",
            "Content-Type",
            "X-Requested-With"
        ));

        // Allow credentials (cookies, auth headers)
        config.setAllowCredentials(true);

        // Max age for preflight cache
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);

        return new CorsFilter(source);
    }
}
```

---

## 9. Security Headers

```java
@Configuration
public class SecurityHeadersConfig {

    @Bean
    public WebSecurityCustomizer webSecurityCustomizer() {
        return (web) -> web.httpFirewall(defaultHttpFirewall());
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.headers()
            // Prevent clickjacking
            .frameOptions().deny()
            // XSS protection
            .xssProtection().block(true)
            // Content type sniffing
            .contentTypeOptions()
            // HSTS (HTTPS only)
            .httpStrictTransportSecurity()
                .maxAgeInSeconds(31536000)
                .includeSubDomains(true)
            .and()
            // Content Security Policy
            .contentSecurityPolicy(
                "default-src 'self'; " +
                "script-src 'self'; " +
                "style-src 'self' 'unsafe-inline'; " +
                "img-src 'self' data:; " +
                "font-src 'self';"
            );

        return http.build();
    }
}
```

---

## 10. Security Checklist

### 10.1 Development Checklist

```
□ Authentication
  □ JWT implemented with secure secret
  □ Token expiration configured
  □ Refresh token mechanism working
  □ Password hashing with BCrypt

□ Authorization
  □ Role-based access control
  □ Resource-level authorization
  □ Admin endpoints protected

□ Input Validation
  □ All API inputs validated
  □ File uploads validated
  □ SQL injection prevention

□ Data Protection
  □ Sensitive data masked in logs
  □ HTTPS configured (production)
  □ Secure token storage

□ Rate Limiting
  □ Auth endpoints rate limited
  □ API endpoints rate limited
  □ File upload rate limited

□ Security Headers
  □ CORS properly configured
  □ CSP headers set
  □ XSS protection enabled
```

### 10.2 Pre-Deployment Checklist

```
□ Change all default secrets
□ Enable HTTPS
□ Configure production CORS origins
□ Review rate limits
□ Enable security logging
□ Test authentication flow
□ Test authorization rules
□ Verify file validation
□ Check for sensitive data exposure
```

---

*Document created as part of CV Assistant Research Project documentation.*
