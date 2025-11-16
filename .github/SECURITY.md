# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in Ardit BioCore, please follow responsible disclosure practices.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via email to:

**Email**: amishra7599@gmail.com  
**Subject**: [SECURITY] Brief description of the issue

### What to Include

Please include as much information as possible:

1. **Description**: Clear description of the vulnerability
2. **Impact**: What could an attacker potentially do?
3. **Reproduction**: Step-by-step instructions to reproduce
4. **Affected Versions**: Which versions are affected?
5. **Suggested Fix**: If you have ideas for fixing (optional)
6. **Proof of Concept**: Code or demonstration (if applicable)

### Example Security Report

```
Subject: [SECURITY] Code injection via SMILES input

Description:
Unsanitized SMILES input could potentially allow code execution
through [specific mechanism].

Impact:
An attacker could execute arbitrary Python code by providing
a specially crafted SMILES string.

Reproduction:
1. Navigate to [page]
2. Enter SMILES: [malicious input]
3. Observe [result]

Affected Versions:
1.0.x through 1.2.0

Suggested Fix:
Add input validation using [method]
```

## Response Timeline

We aim to respond to security reports according to this timeline:

- **Initial Response**: Within 48 hours
- **Severity Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Patch Development**: Depends on severity and complexity
- **Public Disclosure**: After patch is released

## Severity Levels

We assess vulnerabilities using the following criteria:

### Critical

- Remote code execution
- SQL injection
- Authentication bypass
- Data exfiltration

**Response**: Immediate patch, emergency release

### High

- Cross-site scripting (XSS)
- Privilege escalation
- Sensitive data exposure
- Denial of service

**Response**: Patch within 7 days, expedited release

### Medium

- Information disclosure (non-sensitive)
- Moderate impact vulnerabilities
- Security misconfigurations

**Response**: Patch within 30 days, next regular release

### Low

- Minor information leaks
- Best practice violations
- Theoretical vulnerabilities

**Response**: Patch within 90 days, future release

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Virtual Environments**: Isolate dependencies
3. **Input Validation**: Validate SMILES/FASTA before processing
4. **Access Control**: Don't expose API endpoints publicly without authentication
5. **Data Privacy**: Don't process proprietary molecules on public deployments

### For Developers

1. **Input Sanitization**: Always validate user input
   ```python
   from rdkit import Chem
   
   def validate_smiles(smiles: str) -> bool:
       """Safely validate SMILES input."""
       try:
           mol = Chem.MolFromSmiles(smiles)
           return mol is not None
       except:
           return False
   ```

2. **Dependency Management**: 
   - Keep dependencies updated
   - Monitor security advisories for RDKit, NumPy, etc.
   - Use `pip-audit` to check for known vulnerabilities

3. **Secret Management**:
   - Never commit API keys or secrets
   - Use environment variables for sensitive data
   - Don't log sensitive information

4. **Error Handling**:
   - Don't expose internal paths in error messages
   - Sanitize stack traces before displaying to users
   - Log security events for monitoring

## Known Security Considerations

### RDKit Molecule Parsing

**Issue**: RDKit can consume significant memory/CPU on malformed SMILES  
**Mitigation**: Input length limits, timeouts on molecular processing

### FastAPI Endpoints

**Issue**: Unauthenticated API endpoints  
**Status**: By design for research use; production deployments should add auth

### Batch Processing

**Issue**: Large file uploads could cause resource exhaustion  
**Mitigation**: File size limits, rate limiting recommended for production

## Security Updates

Security patches will be:

1. Released as patch versions (e.g., 1.2.1)
2. Announced in CHANGELOG.md with `[SECURITY]` tag
3. Described in GitHub Security Advisories
4. Notified to users who watch the repository

## Disclosure Policy

When a security issue is fixed:

1. **Private Fix**: Develop and test patch privately
2. **Release**: Push fixed version to GitHub
3. **Advisory**: Publish GitHub Security Advisory
4. **Credit**: Acknowledge reporter (if they wish)
5. **Public Disclosure**: Full details 30 days after patch release

## Security Tools

### Recommended Security Checks

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit

# Static security analysis
pip install bandit
bandit -r models/ utils/ features/ api/

# Dependency checking
pip install safety
safety check

# Code quality (includes some security checks)
flake8 --select=E,W,F,C,N
```

### Continuous Security

We use GitHub's security features:

- Dependabot alerts for vulnerable dependencies
- Code scanning with CodeQL (if enabled)
- Secret scanning to prevent credential commits

## Bug Bounty

We currently do not offer a formal bug bounty program. However, we deeply appreciate security researchers who responsibly disclose vulnerabilities and will:

- Acknowledge your contribution in release notes
- List you in our security hall of fame (if desired)
- Provide a letter of recognition (upon request)

## Contact

For security concerns:

**Email**: amishra7599@gmail.com  
**PGP Key**: [If available]  
**GitHub**: [@ardit-mishra](https://github.com/ardit-mishra)

For general bugs (non-security): [GitHub Issues](https://github.com/ardit-mishra/ardit-biocore/issues)

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra

Thank you for helping keep Ardit BioCore secure! 🔒
