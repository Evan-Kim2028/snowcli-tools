# 5-Minute Quickstart - Nanuk MCP

**Goal**: Get from zero to running your first Snowflake query via MCP in 5 minutes

**Prerequisites**:
- ✅ Python 3.12+ installed
- ✅ Snowflake account credentials (username/password)
- ✅ MCP-compatible client (Claude Code, Continue, or any MCP client)

---

## Step 1: Install (1 minute)

```bash
# Install both packages at once
pip install nanuk-mcp snowflake-cli-labs
```

**Verify**:
```bash
snow --version  # Should show version
python -c "import nanuk_mcp; print(nanuk_mcp.__version__)"  # Should show 2.0.0
```

---

## Step 2: Create Snowflake Profile (2 minutes)

**You'll need** (ask your Snowflake admin if you don't know):
- Account identifier (e.g., `mycompany-prod.us-east-1`)
- Username
- Password
- Warehouse name (e.g., `COMPUTE_WH`)

**Run this command** (replace `<...>` with your values):
```bash
snow connection add \
  --connection-name "quickstart" \
  --account "<your-account>.<region>" \
  --user "<your-username>" \
  --password \
  --warehouse "<your-warehouse>"
```

**Example**:
```bash
snow connection add \
  --connection-name "quickstart" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --password \
  --warehouse "COMPUTE_WH"
# Enter password when prompted
```

**Verify**:
```bash
snow connection test --connection-name "quickstart"
# Should show "Connection successful"
```

---

## Step 3: Configure Your MCP Client (1 minute)

**Configuration varies by client**. Add this MCP server configuration:

**Server Configuration**:
```json
{
  "mcpServers": {
    "snowflake": {
      "command": "nanuk-mcp",
      "args": ["--profile", "quickstart"]
    }
  }
}
```

**Common MCP Clients**:

<details>
<summary>Claude Code (Click to expand)</summary>

**Config file location**:
```bash
# macOS/Linux:
~/Library/Application Support/Claude/claude_desktop_config.json

# Windows:
%APPDATA%\Claude\claude_desktop_config.json
```

Restart Claude Code after editing.
</details>

<details>
<summary>Continue (VS Code Extension)</summary>

**Config file location**:
```bash
# macOS/Linux:
~/.continue/config.json

# Windows:
%USERPROFILE%\.continue\config.json
```

Reload VS Code window after editing.
</details>

<details>
<summary>Zed Editor</summary>

**Config via Settings UI**:
1. Open Zed → Settings → MCP Servers
2. Add server with command `nanuk-mcp` and args `["--profile", "quickstart"]`

Or edit config file directly:
```bash
~/.config/zed/settings.json
```
</details>

<details>
<summary>Other MCP Clients</summary>

Refer to your client's documentation for MCP server configuration.
The server configuration is always:
- Command: `nanuk-mcp`
- Args: `["--profile", "quickstart"]`
</details>

---

## Step 4: Test It! (1 minute)

**In your MCP client, ask**:
```
Show me my Snowflake databases
```

Your AI assistant will use the `execute_query` tool and show your databases! 🎉

**Try more queries**:
```
What tables are in my database?
```

```
Show me a sample of data from [your-table-name]
```

```
Profile the table CUSTOMERS for me
```

---

## Success! What Next?

### Improve Security (Recommended)

Replace password auth with key-pair:

1. Generate keys:
```bash
mkdir -p ~/.snowflake
openssl genrsa -out ~/.snowflake/key.pem 2048
openssl rsa -in ~/.snowflake/key.pem -pubout -out ~/.snowflake/key.pub
chmod 400 ~/.snowflake/key.pem
```

2. Upload public key to Snowflake:
```bash
# Print formatted key:
cat ~/.snowflake/key.pub | grep -v "BEGIN\|END" | tr -d '\n'

# In Snowflake, run:
ALTER USER your_username SET RSA_PUBLIC_KEY='<paste_key_here>';
```

3. Update profile:
```bash
snow connection add \
  --connection-name "quickstart" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "COMPUTE_WH"
```

### Explore Features

- **Catalog building**: Ask your AI to "build a catalog of my database"
- **Data lineage**: Ask "what's the lineage for table X?"
- **Table profiling**: Ask "profile table X for me"
- **Dependency graphs**: Ask "show me dependencies for my database"

### Learn More

- Full documentation: `/docs/getting-started.md`
- Parameter guide: `/examples/2.0_user_experience/01_parameter_clarity.md`
- Troubleshooting: `/examples/2.0_user_experience/03_common_errors.md`

---

## Troubleshooting

**Can't find account identifier?**

Your Snowflake URL is like:
```
https://abc12345.us-east-1.snowflakecomputing.com
```

Your account identifier is:
```
abc12345.us-east-1
```
(everything before `.snowflakecomputing.com`)

**Profile not found?**

Check profile exists:
```bash
snow connection list
```

Use exact name in Claude Code config.

**Queries failing?**

Make sure warehouse was specified:
```bash
snow connection test --connection-name "quickstart"
# Check output mentions warehouse
```

**MCP client not showing tools?**

1. Check config file syntax (valid JSON)
2. Restart your MCP client completely
3. Check nanuk-mcp is in PATH: `which nanuk-mcp`
4. Check MCP server logs for errors

---

**Total time**: 5 minutes ⏱️

**🐻‍❄️ You're ready to explore Snowflake with AI! Happy querying!**
