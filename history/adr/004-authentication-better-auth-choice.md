# ADR 004: Authentication Framework (Better-Auth)

**Status**: Accepted
**Date**: 2025-12-24
**Deciders**: Lead Architect, Auth & Personalization Specialist
**Consulted**: Backend Engineer
**Informed**: All subagents

---

## Context

The project requires user authentication (signup, signin, logout) with email verification. Many options exist: Firebase, Auth0, Better-Auth, Keycloak, custom JWT, etc.

### Options Considered

#### Option A: Firebase Authentication
- **Pros**:
  - Managed service (zero ops)
  - Many built-in providers (Google, GitHub, Facebook)
  - Email verification built-in
  - Session management automatic
  - Mobile SDK support
- **Cons**:
  - Vendor lock-in (hard to migrate)
  - Limited customization
  - Overkill for simple email/password (we don't need social login)
  - Cost at scale (per-auth pricing)
  - Data stored in Google infrastructure (privacy concerns)

#### Option B: Auth0
- **Pros**:
  - Industry standard
  - Highly customizable
  - Many integrations
  - Enterprise features
- **Cons**:
  - Expensive (starting $99/mo)
  - Overkill for hackathon project
  - Vendor lock-in
  - Slower setup (complex config)

#### Option C: Keycloak (Self-Hosted)
- **Pros**:
  - Open source, self-hosted
  - Full control
  - No vendor lock-in
  - Enterprise features
- **Cons**:
  - High operational complexity (self-hosting)
  - Over-engineered for simple use case
  - Requires ops expertise
  - Deployment overhead

#### Option D: Custom JWT (Backend-Only)
- **Pros**:
  - Full control
  - No external dependencies
  - Simple implementation
  - Cheap
- **Cons**:
  - Must handle security carefully (password hashing, token expiry, etc.)
  - Missing features (email verification, password reset)
  - Maintenance burden
  - Higher risk of security bugs

#### Option E: Better-Auth (Open Source, Modern)
- **Pros**:
  - Modern, designed for Next.js/modern stacks
  - Email/password + email verification
  - Session management built-in
  - Open source (self-hostable, no lock-in)
  - Lightweight (lower overhead than Auth0/Firebase)
  - Works with any backend (REST, GraphQL)
  - Password reset, OAuth providers (optional)
  - Zero ops (integrates with your DB)
- **Cons**:
  - Newer, smaller community than Firebase/Auth0
  - Less documentation/examples
  - Requires own email service provider (Sendgrid, etc.)
  - Community support might be slower

---

## Decision

**Use Better-Auth for authentication.**

### Rationale

1. **Right-Sized Solution**: We only need email/password + email verification. Better-Auth provides exactly this without overkill.

2. **No Vendor Lock-In**: Open source, works with any database/backend. Easy to migrate later if needed.

3. **Modern Stack Fit**: Better-Auth designed for modern web apps (React, TypeScript, REST APIs). Integrates seamlessly with our FastAPI + React stack.

4. **Cost-Effective**: Free, no per-auth pricing. Operational costs only (email provider like Sendgrid, cheap).

5. **Security**: Handles password hashing (bcrypt), token expiry, session management correctly. Designed by security-conscious developers.

6. **Simplicity**: Setup in 1-2 days. Clear documentation. No complex configuration.

7. **Flexibility**: Can add OAuth providers later if needed (Google, GitHub). Email verification required by default.

---

## Consequences

### Positive
- ✅ Lightweight, no vendor lock-in
- ✅ Cost-effective (free auth, pay for email)
- ✅ Fast setup (1-2 days)
- ✅ Secure by default (bcrypt, token expiry, rate limiting)
- ✅ Modern, well-designed API
- ✅ Works with our stack (FastAPI, React, TypeScript)
- ✅ Email verification built-in
- ✅ Session management automatic

### Negative
- ⚠️ **Newer project**: Smaller community, less StackOverflow answers
- ⚠️ **Documentation**: Not as comprehensive as Firebase/Auth0
- ⚠️ **Email service**: Must set up external email provider (Sendgrid, AWS SES, etc.)
- ⚠️ **Custom features**: If we need advanced features (MFA, SAML, etc.), might need customization
- ⚠️ **Support**: No dedicated support team (community-driven)

### Mitigation Strategies
1. **Documentation**: Reference Better-Auth docs + FastAPI docs together
2. **Email provider**: Use Sendgrid free tier (500 emails/month, sufficient for hackathon)
3. **Custom features**: Not needed for MVP; can add in Phase 4 if time permits
4. **Support**: Community Discord/GitHub issues responsive

---

## Implementation

### Setup Overview
1. Install Better-Auth package in FastAPI backend
2. Configure with Neon Postgres database
3. Create User model (email, password_hash, profile fields)
4. Implement signup/signin/logout endpoints
5. Frontend form components (LoginForm, SignupForm)
6. Token storage (localStorage or secure cookies)
7. Protected route middleware

### Email Configuration
- Email provider: SendGrid (free tier: 100 emails/day)
- Email template: SendGrid transactional email template
- Sender: no-reply@textbook-domain
- Verification link: sent immediately on signup

### Token Strategy
- JWT tokens (signed with secret)
- Token expiry: 30 days (long, suitable for learning platform)
- Refresh tokens: optional (not needed if expiry long)
- Storage: localStorage with httpOnly cookie for auth header

---

## Related Decisions

- **PLAN Phase 0.5**: Better-Auth setup details
- **PLAN Phase 1.4**: Authentication integration
- **PLAN Phase 2.1**: User profiling (extends auth with background fields)

---

## Approval

- ✅ **Lead Architect**: Approved (right-sized, cost-effective, no lock-in)
- ✅ **Auth & Personalization Specialist**: Approved (modern, well-designed, secure defaults)
- ✅ **Backend Engineer**: Approved (easy integration with FastAPI)

---

## References

- Better-Auth: https://www.better-auth.com/
- SendGrid: https://sendgrid.com/
- JWT Best Practices: https://tools.ietf.org/html/rfc7519

