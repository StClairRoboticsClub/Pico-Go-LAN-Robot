# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

The Pico-Go LAN Robot team takes security bugs seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Contact**: Jeremy Dueck
- **Organization**: St. Clair College Robotics Club
- **Email**: [INSERT EMAIL HERE]

### What to Include

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Acknowledgment**: Within 48 hours of receiving your report
- **Initial Assessment**: Within 5 business days
- **Status Update**: Every 7 days until resolution
- **Fix Release**: Depends on severity and complexity

### Disclosure Policy

- Security advisories will be published on the GitHub Security Advisory page
- We will credit reporters who responsibly disclose vulnerabilities (unless you prefer to remain anonymous)
- We request that you do not publicly disclose the vulnerability until we have issued a fix

## Security Best Practices

When deploying this robot system:

1. **Network Security**
   - Use strong WPA2 passwords for Wi-Fi hotspots
   - Keep robot on isolated network (do not connect to internet)
   - Change default credentials in `firmware/config.py`

2. **Physical Security**
   - Robots should be operated in controlled environments
   - Emergency stop button should be easily accessible
   - Monitor battery voltage to prevent over-discharge

3. **Code Security**
   - Review all firmware changes before deployment
   - Do not commit sensitive credentials to git
   - Keep MicroPython and dependencies up to date

4. **Safety Systems**
   - Watchdog timeout is critical - do not disable
   - Test fail-safe behavior regularly
   - Verify motor directions before competitive use

## Known Security Considerations

### By Design
- **No Authentication**: The TCP control protocol (port 8765) has no authentication. This is acceptable for isolated competition environments but should not be exposed to untrusted networks.
- **No Encryption**: Control commands are sent in plaintext JSON. For educational/competition use on isolated networks, this is acceptable.
- **Single Controller**: Only one controller can connect at a time. Additional connections will be rejected.

### Mitigations
- System operates on air-gapped networks (no internet)
- Physical access required to change firmware
- Watchdog provides fail-safe motor cutoff

## Contact

For non-security-related issues, please use the GitHub Issues page.

---

**Last Updated**: 2025-11-06  
**Security Policy Version**: 1.0
