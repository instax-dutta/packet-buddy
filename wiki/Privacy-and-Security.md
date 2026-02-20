# Privacy & Security

PacketBuddy is built with a **privacy-first philosophy**. This document explains exactly how your data is handled, what we collect (and don't collect), and how you can maintain control over your information.

---

## Privacy Principles

### Local-First Data Storage

**YOUR data never leaves YOUR machine unless YOU want it to.**

PacketBuddy operates on a local-first architecture:

- All network usage data is stored in a local SQLite database on your machine
- No data is transmitted to external servers unless you explicitly enable cloud sync
- You maintain complete ownership and control of your data at all times
- The application functions fully offline with no internet connection required

### No Telemetry or Tracking

**Zero analytics, no telemetry, no data collection whatsoever.**

- No usage analytics are collected
- No crash reports are sent automatically
- No "phone home" functionality exists in the codebase
- No third-party tracking services are integrated
- The application does not connect to any external servers by default

### No PII Collection

**No websites, apps, or personal data collected.**

PacketBuddy deliberately limits data collection to non-personal metrics:

| What We DO Collect | What We DON'T Collect |
|--------------------|----------------------|
| Bytes sent/received | Websites visited |
| Timestamps of activity | Applications used |
| Network interface names | Personal identifiers |
| Session duration metadata | IP addresses (external) |
| | Browsing history |
| | Account credentials |
| | File contents |

---

## Security Features

### Local-Only API Binding (127.0.0.1)

The PacketBuddy API server binds exclusively to `127.0.0.1` (localhost):

```
API URL: http://127.0.0.1:7373
Dashboard: http://127.0.0.1:7373/dashboard
```

**Why this matters:**

- The API is only accessible from your local machine
- External devices on your network cannot access the API
- Remote attackers cannot reach the API over the internet
- No port forwarding or firewall configuration required

### No External Exposure

By design, PacketBuddy has no external attack surface:

- **No open ports** to the internet
- **No external API endpoints** exposed
- **No webhooks** or callback URLs
- **No background services** that phone home
- **No browser extensions** that could leak data

### Optional Cloud Sync

Cloud synchronization is entirely opt-in:

- Disabled by default
- Requires explicit configuration of your own NeonDB instance
- No shared infrastructure with other users
- Complete isolation of your data

---

## Data Collected

### What IS Collected

PacketBuddy collects minimal, non-personal network metrics:

| Data Point | Purpose | Retention |
|------------|---------|-----------|
| Bytes sent | Track upload usage | Local: indefinitely, Cloud: per policy |
| Bytes received | Track download usage | Local: indefinitely, Cloud: per policy |
| Timestamp | Record when usage occurred | Local: indefinitely, Cloud: per policy |
| Network interface | Identify which adapter was used | Local: indefinitely, Cloud: per policy |
| Session ID | Group related data points | Local: until aggregation, Cloud: none |

### What is NOT Collected

PacketBuddy deliberately does NOT collect:

- **Web browsing data**: No URLs, domains, or website content
- **Application data**: No app names, process names, or app usage patterns
- **Personal information**: No names, emails, phone numbers, or addresses
- **Authentication data**: No passwords, tokens, or credentials
- **Location data**: No GPS coordinates or IP geolocation
- **File contents**: No data about files on your system
- **Communication content**: No message contents or call data

---

## NeonDB Cloud Sync

### How It Works

When enabled, cloud sync provides cross-device access to your usage data:

1. **Your Instance**: You create and own a free NeonDB PostgreSQL instance
2. **Encrypted Transit**: All data is encrypted via TLS during transmission
3. **Batch Synchronization**: Data is sent in optimized batches to minimize costs
4. **Scale-to-Zero Compatible**: Designed for free tier instances that sleep when inactive

**Synchronization Flow:**

```
Local SQLite → Batch Aggregation → TLS Encryption → Your NeonDB Instance
```

### Your Own Instance

You maintain complete control over your cloud data:

- **You create** the NeonDB account (free tier available)
- **You configure** the connection in PacketBuddy
- **You own** all data in the database
- **You can delete** the database at any time
- **We never see** or have access to your data

**Setting Up Your Instance:**

1. Create a free account at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Add to PacketBuddy configuration

### Data Encryption in Transit

All data transmitted to NeonDB is protected:

- **TLS 1.2+ Encryption**: Industry-standard transport encryption
- **Certificate Validation**: Full certificate chain verification
- **No Custom Encryption Needed**: NeonDB handles encryption transparently

---

## Data Retention

### Local Retention Policies

Data stored locally follows an intelligent retention strategy:

| Data Type | Retention Period | Reason |
|-----------|------------------|--------|
| Raw usage logs | 90 days | Detailed analysis of recent usage |
| Hourly aggregates | 2 years | Medium-term trend analysis |
| Daily aggregates | Indefinitely | Long-term historical trends |
| Monthly aggregates | Indefinitely | Year-over-year comparisons |

**Storage Footprint:**

- Typical daily usage: ~50 KB
- Monthly data: ~1.5 MB
- Yearly data: ~18 MB (after aggregation)

### Cloud Retention Policies

Cloud retention is controlled by your configuration:

| Setting | Default | Options |
|---------|---------|---------|
| Raw data retention | 30 days | Configurable |
| Aggregate retention | 2 years | Configurable |
| Auto-cleanup | Enabled | Can be disabled |

**Manual Control:**

You can manually delete cloud data at any time:

- Via NeonDB dashboard (drop tables)
- Via PacketBuddy CLI (`pb cleanup --cloud`)
- By deleting your NeonDB project entirely

---

## Security Best Practices

### For All Users

1. **Keep PacketBuddy Updated**
   ```bash
   pb update
   ```
   Regular updates include security patches.

2. **Review Configuration**
   - Check `config.json` for unexpected settings
   - Verify no unintended cloud sync is enabled

3. **Protect Local Database**
   - The SQLite database contains your usage data
   - Default location: `%APPDATA%\PacketBuddy\data\` (Windows) or `~/.packetbuddy/data/` (Linux/macOS)
   - Back up this directory if you want to preserve history

### For Cloud Sync Users

1. **Secure Your NeonDB Credentials**
   - Never commit connection strings to version control
   - Use environment variables when possible
   - Rotate credentials if compromised

2. **Monitor Access**
   - Review NeonDB dashboard for unexpected connections
   - Enable audit logging if available

3. **Network Security**
   - Sync only over trusted networks
   - Avoid syncing over public WiFi

### For Advanced Users

1. **Firewall Configuration**
   ```bash
   # Verify API is only accessible locally
   netstat -an | findstr 7373
   ```
   Should show only `127.0.0.1:7373` bindings.

2. **Process Isolation**
   - Run PacketBuddy under a dedicated user account
   - Restrict file system permissions to necessary directories

3. **Audit Logs**
   - PacketBuddy logs all sync operations
   - Review logs periodically: `pb logs`

---

## Privacy FAQ

### General Questions

**Q: Does PacketBuddy send any data to external servers by default?**

A: No. PacketBuddy operates entirely locally. No data leaves your machine unless you explicitly configure cloud sync with your own NeonDB instance.

**Q: Can the developers see my data?**

A: No. We have no access to your local data, and cloud sync uses your own NeonDB instance that we cannot access.

**Q: Is my browsing history collected?**

A: No. PacketBuddy only tracks bytes transferred, not which websites you visit or what content you access.

**Q: Does PacketBuddy know which apps I'm using?**

A: No. We track network interface activity, not individual application usage.

### Cloud Sync Questions

**Q: Is cloud sync required?**

A: No. Cloud sync is completely optional. PacketBuddy works fully offline.

**Q: Who owns my cloud data?**

A: You do. The NeonDB instance is registered to your account, and we have no access to it.

**Q: Can I use a different database provider?**

A: Currently, PacketBuddy supports NeonDB (PostgreSQL). Support for other providers may be added in future versions.

**Q: What happens if I delete my NeonDB account?**

A: All cloud data is permanently deleted. Your local data remains intact.

### Data Questions

**Q: How much disk space does local data use?**

A: Typically 18-50 MB per year, thanks to intelligent aggregation of historical data.

**Q: Can I export my data?**

A: Yes. Use `pb export --format html` for a human-readable report, or access the SQLite database directly.

**Q: Can I delete specific data?**

A: Yes. You can delete local data via the CLI (`pb cleanup`) or by directly modifying the SQLite database.

**Q: Is the local database encrypted?**

A: The SQLite database is not encrypted by default. If you need encryption, consider using full-disk encryption (BitLocker, FileVault, LUKS).

### Security Questions

**Q: Can someone on my network access PacketBuddy?**

A: No. The API binds only to 127.0.0.1, making it accessible only from your local machine.

**Q: What if I find a security vulnerability?**

A: Please report it responsibly via GitHub Issues. We take security seriously and will respond promptly.

**Q: Is PacketBuddy open source?**

A: Yes. You can audit the entire codebase on GitHub.

**Q: Are there any known security issues?**

A: Check our [GitHub Issues](https://github.com/instax-dutta/packet-buddy/issues) for any reported vulnerabilities and their status.

---

## Summary

| Aspect | Implementation |
|--------|----------------|
| Data Location | Local-first, your machine |
| External Access | None by default |
| PII Collection | None |
| Tracking/Telemetry | None |
| Cloud Sync | Optional, your own instance |
| API Exposure | Localhost only (127.0.0.1) |
| Encryption | TLS for cloud sync |
| Open Source | Yes, fully auditable |

**Your data. Your control. Your privacy.**

---

*Last Updated: 2026-02-21 | Version: 1.4.3*
