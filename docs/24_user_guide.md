# 24. User Guide - Hướng Dẫn Sử Dụng

> **Document Version**: 1.0
> **Last Updated**: 2026-01-24
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [17_api_specifications.md](./17_api_specifications.md), [21_chatbot_specification.md](./21_chatbot_specification.md)

---

## 1. Getting Started

### 1.1 What is CV Assistant?

CV Assistant is an AI-powered conversational system that helps you:

- **Analyze your CV**: Extract and understand information from your resume
- **Match skills with jobs**: Compare your skills against job descriptions
- **Get career advice**: Receive personalized career path recommendations
- **Improve your CV**: Get tips on how to enhance your resume

### 1.2 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Browser | Chrome 90+, Firefox 88+, Safari 14+ | Latest version |
| Internet | 1 Mbps | 5+ Mbps |
| Screen | 1024 x 768 | 1920 x 1080 |
| JavaScript | Enabled | Enabled |

---

## 2. Account Management

### 2.1 Creating an Account

1. Navigate to the CV Assistant homepage
2. Click **"Sign Up"** button
3. Fill in your information:
   - Email address
   - Password (minimum 8 characters, must include uppercase, lowercase, and number)
   - Full name
4. Click **"Create Account"**
5. Check your email for verification (if enabled)

### 2.2 Logging In

1. Go to the login page
2. Enter your email and password
3. Click **"Log In"**
4. You will be redirected to the main chat interface

### 2.3 Forgot Password

1. Click **"Forgot Password?"** on the login page
2. Enter your registered email
3. Check your email for reset instructions
4. Follow the link to create a new password

---

## 3. Main Interface

### 3.1 Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CV Assistant                        [Logout] │
├────────────────┬────────────────────────────────────────────────┤
│                │                                                 │
│  Threads       │           Conversation Area                    │
│  ──────────    │                                                 │
│  □ New Chat    │   ┌─────────────────────────────────────────┐  │
│                │   │ AI: Hello! I'm your CV Assistant.       │  │
│  Recent:       │   │ How can I help you today?               │  │
│  ├─ Career     │   └─────────────────────────────────────────┘  │
│  │  advice     │                                                 │
│  ├─ CV review  │   ┌─────────────────────────────────────────┐  │
│  │  session    │   │ You: I'd like to analyze my CV          │  │
│  └─ Skill      │   └─────────────────────────────────────────┘  │
│    matching    │                                                 │
│                │                                                 │
│                ├─────────────────────────────────────────────────┤
│                │ [📎 Attach] Type your message...     [Send ▶]  │
└────────────────┴─────────────────────────────────────────────────┘
```

### 3.2 Sidebar

- **New Chat**: Start a fresh conversation
- **Recent Threads**: Access previous conversations
- **Thread Actions**: Rename or delete threads (hover to reveal)

### 3.3 Conversation Area

- View AI responses and your messages
- Results from CV analysis are displayed inline
- Skill matching results show in formatted cards

### 3.4 Message Composer

- Type your message in the input field
- Click the attachment button (📎) to upload CV
- Press Enter or click Send (▶) to send message

---

## 4. Core Features

### 4.1 CV Analysis

**How to analyze your CV:**

1. Click the attachment button (📎)
2. Select your CV file (PDF format, max 10MB)
3. The system will upload and analyze your CV
4. AI will extract and display:
   - Personal information summary
   - Work experience
   - Education
   - Skills
   - Projects
   - Certifications

**Example interaction:**

```
You: [Uploads CV.pdf]

AI: I've analyzed your CV. Here's what I found:

📋 **CV Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Experience**: 3 years in software development

🏢 **Organizations**:
   • Google Inc. (2023-Present)
   • ABC Tech (2021-2023)

🎓 **Education**:
   • B.S. Computer Science, MIT (2021)

💡 **Skills** (12 found):
   Python, Java, JavaScript, React, Docker,
   Kubernetes, AWS, SQL, Machine Learning,
   Git, Agile, CI/CD

🏆 **Certifications**:
   • AWS Solutions Architect

Would you like me to:
1. Match your skills with a job description?
2. Suggest improvements to your CV?
3. Recommend career paths based on your profile?
```

### 4.2 Skill Matching

**How to match skills with a job:**

1. First, upload your CV (or use a previously uploaded one)
2. Ask to match with a job description
3. Paste or describe the job requirements
4. Get detailed matching analysis

**Example interaction:**

```
You: Can you match my CV with this job?

Software Engineer at TechCorp:
- Required: Python, Java, AWS, Docker
- Nice to have: Kubernetes, Machine Learning
- Experience: 3+ years

AI: Here's your skill match analysis:

📊 **Match Score: 92%**

✅ **Exact Matches** (4/4 required):
   • Python ✓
   • Java ✓
   • AWS ✓
   • Docker ✓

✅ **Bonus Matches** (2/2 nice-to-have):
   • Kubernetes ✓
   • Machine Learning ✓

✅ **Experience**: You have 3 years (meets requirement)

💡 **Recommendation**: You're an excellent match for this role!
   Your profile exceeds all requirements. I suggest
   highlighting your Kubernetes and ML experience in
   your cover letter as these are differentiators.
```

### 4.3 Career Recommendations

**How to get career advice:**

1. Upload your CV or describe your current role
2. Tell the AI your career goals
3. Receive personalized path recommendations

**Example interaction:**

```
You: I'm currently a Mid-level Developer. I want to
become a Tech Lead. What should I do?

AI: Based on your profile, here's a career roadmap:

🎯 **Goal**: Mid-level Developer → Tech Lead

📈 **Recommended Path** (Conservative, 3-4 years):

**Stage 1: Senior Developer** (1.5-2 years)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skills to develop:
  • System Design (you have: basic → need: intermediate)
  • Code Review (start leading reviews)
  • Mentoring (mentor 1-2 junior developers)

Actions:
  • Lead a medium-sized project
  • Present at team tech talks
  • Consider: AWS Solutions Architect certification

**Stage 2: Tech Lead** (1.5-2 years)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skills to develop:
  • Team Management
  • Technical Decision Making
  • Stakeholder Communication

Actions:
  • Lead a cross-functional project
  • Participate in hiring decisions
  • Define technical standards for team

Would you like more details on any stage?
```

### 4.4 CV Improvement Tips

**How to get CV tips:**

1. Upload your CV
2. Ask for improvement suggestions
3. Receive specific, actionable feedback

**Example interaction:**

```
You: How can I improve my CV?

AI: Here are my suggestions for your CV:

📝 **Improvement Recommendations**

**1. Professional Summary** ⚠️
   Current: Missing
   Suggestion: Add a 3-4 sentence summary highlighting
   your experience and key achievements.

   Example:
   "Results-driven Software Engineer with 3+ years of
   experience in full-stack development. Proven track
   record of delivering scalable applications serving
   100K+ users. Expertise in Python, Java, and cloud
   technologies."

**2. Work Experience** ✅ Good, but can improve
   • Add metrics to your achievements
   • Current: "Developed web application"
   • Better: "Developed web application serving 50K
     daily users, reducing load time by 40%"

**3. Skills Section** ✅ Well organized
   Suggestion: Group by category (Languages, Frameworks,
   Tools) for better readability.

**4. Projects** ⚠️ Missing
   Add 2-3 notable projects with:
   • Project name and description
   • Technologies used
   • Your role and impact

Would you like me to help rewrite any section?
```

---

## 5. Conversation Tips

### 5.1 Effective Prompts

| Goal | Good Prompt | Why It Works |
|------|-------------|--------------|
| Analyze CV | "Analyze my CV and summarize my profile" | Clear, specific request |
| Skill match | "Match my skills with this job: [paste JD]" | Provides context |
| Career advice | "I'm a [current role], I want to become [goal]" | Clear starting point and goal |
| CV tips | "What's missing from my CV?" | Open but focused question |

### 5.2 Follow-up Questions

The AI remembers context within a conversation. You can ask follow-ups:

- "Tell me more about the first suggestion"
- "What if I focus on the ambitious path instead?"
- "How do I develop [specific skill]?"
- "Can you help me rewrite my professional summary?"

### 5.3 Starting Fresh

- Click **"New Chat"** to start a conversation without previous context
- This is useful when switching topics completely

---

## 6. Managing Threads

### 6.1 Creating Threads

Every new conversation creates a thread. Threads are auto-named based on the first topic discussed.

### 6.2 Renaming Threads

1. Hover over a thread in the sidebar
2. Click the edit icon (✏️)
3. Enter a new name
4. Press Enter to save

### 6.3 Deleting Threads

1. Hover over a thread in the sidebar
2. Click the delete icon (🗑️)
3. Confirm deletion

**Note**: Deleted threads cannot be recovered.

---

## 7. Data & Privacy

### 7.1 What Data is Stored

| Data Type | Stored | Duration | Purpose |
|-----------|--------|----------|---------|
| Account info | Yes | Until deletion | Authentication |
| Uploaded CVs | Yes | Until deletion | Analysis |
| Chat history | Yes | Until deletion | Conversation context |
| Extracted entities | Yes | Until deletion | Personalization |

### 7.2 Data Security

- All data is encrypted in transit (HTTPS)
- Your CVs are only accessible to you
- We do not share your data with third parties

### 7.3 Deleting Your Data

To delete all your data:
1. Go to Settings
2. Click "Delete Account"
3. Confirm deletion
4. All data will be permanently removed

---

## 8. Troubleshooting

### 8.1 Common Issues

**CV upload fails:**
- Ensure file is PDF format
- File size must be under 10MB
- Try refreshing the page

**AI response is slow:**
- Large CVs take longer to process
- Complex queries require more computation
- Check your internet connection

**Login issues:**
- Clear browser cache and cookies
- Try incognito/private mode
- Reset password if needed

**Session expired:**
- You'll be prompted to log in again
- Your conversation history is preserved

### 8.2 Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Invalid file type" | Only PDFs accepted | Convert your CV to PDF |
| "File too large" | Over 10MB limit | Compress or split the file |
| "Rate limit exceeded" | Too many requests | Wait a few minutes |
| "Session expired" | Login timeout | Log in again |

### 8.3 Getting Help

If you encounter issues:
1. Check this user guide
2. Try refreshing the page
3. Contact support with:
   - Description of the issue
   - Steps to reproduce
   - Browser and OS information

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `Ctrl + N` | New chat |
| `Esc` | Close dialogs |

---

## 10. Best Practices

### 10.1 For Best Results

1. **Use clear, specific questions**
   - "How can I improve my CV for software engineering roles?"
   - Not: "Make my CV better"

2. **Provide context**
   - Upload your CV before asking for personalized advice
   - Share relevant job descriptions for matching

3. **Use follow-ups**
   - Drill down into specific recommendations
   - Ask for clarification when needed

4. **Organize with threads**
   - Use separate threads for different topics
   - Rename threads for easy reference

### 10.2 CV Tips for Better Analysis

- Use a clean, standard PDF format
- Avoid complex layouts or graphics
- Use consistent formatting
- Include clear section headers

---

## 11. FAQ

**Q: What CV format should I use?**
A: PDF format works best. The system can also handle text extracted from most standard CV templates.

**Q: Is my CV data secure?**
A: Yes. All data is encrypted and only accessible to you. We do not share your information.

**Q: Can I use the system in Vietnamese?**
A: Currently, the system is optimized for English CVs. Vietnamese support may be added in future versions.

**Q: How accurate is the skill matching?**
A: The system uses semantic matching, so it understands that "ML" means "Machine Learning". Accuracy depends on how clearly skills are stated in both your CV and the job description.

**Q: Can I export my analysis results?**
A: Currently, you can copy text from the chat. Export functionality may be added in future versions.

**Q: How long is my data kept?**
A: Your data is kept until you delete it or close your account.

---

*Document created as part of CV Assistant Research Project documentation.*
