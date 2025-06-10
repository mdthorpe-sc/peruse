# Website Screenshot Monitoring Tool

A comprehensive tool for taking website screenshots and using AI-powered change detection for deployment monitoring and site availability checks.

## Features

- 🖼️ **High-quality screenshots** using Playwright
- 🤖 **AI-powered change detection** using configurable Claude models via Amazon Bedrock Converse API
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
3. Request access to **Claude models** you want to use
4. The tool supports multiple Claude models with automatic fallback from inference profile to direct model

#### Available Models:
Models are configured in `models.json` file. You can view and customize them:

```bash
# See all available models and their capabilities
python screenshot_monitor.py list-models

# Use custom config file
python screenshot_monitor.py list-models --config my-models.json
```

**Default models included:**
- `claude-4-sonnet` - Latest Sonnet, balanced performance (default)
- `claude-3.5-sonnet` - Enhanced analysis capabilities  
- `claude-3-opus` - Most capable for complex analysis
- `claude-3-haiku` - Fast and cost-effective

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
# Auto-generate name from URL (uses default claude-4-sonnet)
python screenshot_monitor.py baseline https://example.com

# Use custom name and model
python screenshot_monitor.py baseline https://example.com --name mysite --model claude-3.5-sonnet

# Custom viewport
python screenshot_monitor.py baseline https://example.com --name mysite --width 1280 --height 720
```

#### 2. Compare with Baseline

```bash
# Compare with stored baseline using specific model
python screenshot_monitor.py compare https://example.com --name mysite --model claude-3-opus

# Auto-detect baseline from URL (uses default model)
python screenshot_monitor.py compare https://example.com
```

#### 3. List Stored Baselines

```bash
python screenshot_monitor.py list
```

#### 4. List Available Models

```bash
python screenshot_monitor.py list-models
```

## Example Workflow: Deployment Monitoring

```bash
# 1. Before deployment - store baseline with high-quality model
python screenshot_monitor.py baseline https://myapp.com --name production --model claude-3-opus

# 2. After deployment - check for changes with same model  
python screenshot_monitor.py compare https://myapp.com --name production --model claude-3-opus

# 3. For frequent monitoring, use faster model
python screenshot_monitor.py compare https://myapp.com --name production --model claude-3-haiku
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
project/
├── models.json                             # Model configuration
├── screenshot_monitor.py                   # Main monitoring tool
├── screenshot_tool.py                      # Simple screenshot tool
└── screenshots/
    ├── metadata.json                       # Baseline tracking
    ├── example_com_baseline_a1b2c3d4.png  # Baseline screenshot
    ├── example_com_current_1705312245.png # Current screenshot
    └── example_com_report_1705312245.json # Detailed report
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | from config | Claude model to use for analysis |
| `--config` | models.json | Path to model configuration file |
| `--width` | 1920 | Viewport width in pixels |
| `--height` | 1080 | Viewport height in pixels |
| `--storage-dir` | screenshots | Directory for storing files |
| `--aws-region` | us-east-1 | AWS region for Bedrock |

### Model Selection Guide

| Model | Speed | Cost | Analysis Quality | Best For |
|-------|-------|------|------------------|----------|
| `claude-3-haiku` | ⚡⚡⚡ | 💰 | ⭐⭐⭐ | Simple change detection |
| `claude-3-sonnet` | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | Balanced performance |
| `claude-3.5-sonnet` | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐⭐ | Enhanced reasoning |
| `claude-3-opus` | ⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐⭐ | Complex analysis |
| `claude-4-sonnet` | ⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐⭐ | Latest capabilities |
| `claude-4-opus` | ⚡ | 💰💰💰💰 | ⭐⭐⭐⭐⭐⭐⭐ | Most advanced |

### Custom Model Configuration

You can customize the available models by editing `models.json`:

```json
{
  "models": {
    "my-custom-model": {
      "inference_profile": "us.anthropic.claude-custom-model:0",
      "direct": "anthropic.claude-custom-model:0",
      "description": "My custom Claude model",
      "speed": "fast",
      "cost": "low",
      "quality": "excellent"
    }
  },
  "default_model": "my-custom-model",
  "metadata": {
    "version": "1.1",
    "last_updated": "2024-01-15"
  }
}
```

**Required fields for each model:**
- `inference_profile` - Bedrock inference profile ID
- `direct` - Direct Bedrock model ID  
- `description` - Human-readable description

**Optional fields:**
- `speed`, `cost`, `quality` - For documentation/selection guidance

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
   **Solution**: Request access to Claude models in Bedrock console → Model access

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

7. **Configuration File Error**
   ```
   Model configuration file 'models.json' not found
   ```
   **Solution**: Ensure `models.json` exists in your working directory or specify custom path with `--config`

8. **Invalid Model Configuration**
   ```
   Invalid JSON in configuration file
   ```
   **Solution**: Validate your JSON syntax - check for missing commas, quotes, or brackets

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