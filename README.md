# Website Screenshot Monitoring Tool

A comprehensive tool for taking website screenshots and using AI-powered change detection for deployment monitoring and site availability checks.

## Features

- 🖼️ **High-quality screenshots** using Playwright
- 🤖 **AI-powered change detection** using Claude Opus 4 via Amazon Bedrock Converse API
- 📊 **Detailed change reports** with severity levels and recommendations
- 💾 **Baseline storage** with metadata tracking
- 🔍 **Intelligent analysis** of layout, content, styling, and availability changes
- 📁 **Organized storage** with automatic file naming and JSON reports

## Tools Included

### 1. Basic Screenshot Tool (`screenshot_tool.py`)
Simple command-line tool for taking individual screenshots.

### 2. Advanced Monitoring Tool (`screenshot_monitor.py`)
Full-featured monitoring tool with baseline storage and AI comparison.

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- AWS credentials configured

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Browser Binaries

```bash
playwright install
```

### 3. Configure AWS Credentials

Option A - AWS CLI:
```bash
aws configure
```

Option B - Environment Variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 4. Enable Bedrock Model Access

1. Go to AWS Bedrock Console
2. Navigate to "Model access" 
3. Request access to **Claude Opus 4**
4. The tool will automatically try these model identifiers:
   - `us.anthropic.claude-opus-4-20250514-v1:0` (inference profile - preferred)
   - `anthropic.claude-opus-4-20250514-v1:0` (direct model - fallback)

### 5. Verify Setup

```bash
# Run the setup test to verify everything is working
python test_setup.py
```

## Usage

### Basic Screenshot Tool

```bash
# Take a simple screenshot
python screenshot_tool.py https://example.com

# Specify output filename
python screenshot_tool.py https://google.com my_screenshot.png

# Custom viewport size
python screenshot_tool.py https://github.com --width 1280 --height 720
```

### Advanced Monitoring Tool

#### 1. Store a Baseline Screenshot

```bash
# Auto-generate name from URL
python screenshot_monitor.py baseline https://example.com

# Use custom name
python screenshot_monitor.py baseline https://example.com --name mysite

# Custom viewport
python screenshot_monitor.py baseline https://example.com --name mysite --width 1280 --height 720
```

#### 2. Compare with Baseline

```bash
# Compare with stored baseline
python screenshot_monitor.py compare https://example.com --name mysite

# Auto-detect baseline from URL
python screenshot_monitor.py compare https://example.com
```

#### 3. List Stored Baselines

```bash
python screenshot_monitor.py list
```

## Example Workflow: Deployment Monitoring

```bash
# 1. Before deployment - store baseline
python screenshot_monitor.py baseline https://myapp.com --name production

# 2. After deployment - check for changes
python screenshot_monitor.py compare https://myapp.com --name production
```

## Output Examples

### Change Detection Report

```
============================================================
📊 CHANGE DETECTION REPORT
============================================================
Site: example_com
URL: https://example.com
Timestamp: 2024-01-15T10:30:45.123456
Baseline: example_com_baseline_a1b2c3d4.png
Current: example_com_current_1705312245.png
------------------------------------------------------------
Changes Detected: 🔴 YES
Severity: 🟠 MODERATE
Availability: 🟢 AVAILABLE

📝 Summary:
   Navigation menu layout has changed and there are content updates in the main section

🔍 Changes Found:
   1. Type: layout
      Description: Navigation menu items have been rearranged
      Location: Top navigation bar
      Impact: Minor impact on user experience

   2. Type: content
      Description: Main headline text has been updated
      Location: Hero section
      Impact: Content refresh, likely intentional

💡 Recommendations:
   • Verify navigation changes are intentional
   • Check if headline update was planned

📄 Detailed report saved: example_com_report_1705312245.json
============================================================
```

### File Organization

```
screenshots/
├── metadata.json                           # Baseline tracking
├── example_com_baseline_a1b2c3d4.png      # Baseline screenshot
├── example_com_current_1705312245.png     # Current screenshot
└── example_com_report_1705312245.json     # Detailed report
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--width` | 1920 | Viewport width in pixels |
| `--height` | 1080 | Viewport height in pixels |
| `--storage-dir` | screenshots | Directory for storing files |
| `--aws-region` | us-east-1 | AWS region for Bedrock |

## Change Detection Capabilities

The AI analysis detects:

- **Layout Changes**: Element positioning, sizing, visibility
- **Content Changes**: Text updates, image changes
- **Styling Changes**: CSS modifications, color changes
- **Functionality Issues**: Broken elements, error messages
- **Availability Status**: Site accessibility and loading issues

### Severity Levels

- 🟢 **None**: No changes detected
- 🟡 **Minor**: Small cosmetic changes
- 🟠 **Moderate**: Noticeable changes that may need review
- 🔴 **Major**: Significant changes affecting functionality
- 🚨 **Critical**: Site errors or complete unavailability

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```
   Error: AWS credentials not found
   ```
   **Solution**: Configure AWS credentials using `aws configure`

2. **Bedrock Access Denied**
   ```
   Error: Access denied to Bedrock
   ```
   **Solution**: Request access to Claude Opus 4 in Bedrock console → Model access

3. **Model Not Available**
   ```
   Error: Model not found. The inference profile may not be available in your region.
   ```
   **Solution**: Try a different AWS region (us-east-1, us-west-2) or wait for model availability

4. **Inference Profile Error**
   ```
   Invocation of model ID ... with on-demand throughput isn't supported
   ```
   **Solution**: The tool automatically falls back to direct model access - this is handled automatically

5. **Playwright Browser Error**
   ```
   Error: Browser executable not found
   ```
   **Solution**: Run `playwright install`

6. **Large Image Error**
   ```
   Error: Invalid request to Bedrock
   ```
   **Solution**: Reduce viewport size with `--width 1280 --height 720`

### Performance Tips

- Use appropriate viewport sizes (larger = slower)
- Consider network timeouts for slow-loading sites
- Store baselines in accessible locations for automated scripts

## Integration Ideas

- **CI/CD Pipeline**: Run comparisons after deployments
- **Cron Jobs**: Regular site monitoring
- **Alerting**: Parse JSON reports for automated notifications
- **Dashboard**: Build monitoring dashboards from report data

## Cost Considerations

- **Playwright**: Free, runs locally
- **Amazon Bedrock**: Pay per API call (~$0.003 per 1K tokens)
- **Storage**: Minimal local storage for screenshots and reports

## License

MIT License - feel free to modify and use for your projects! 