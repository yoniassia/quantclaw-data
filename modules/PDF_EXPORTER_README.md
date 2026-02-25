# PDF Report Exporter

**Phase 79**: Convert markdown reports to professional PDF with charts and email delivery

## Overview

The PDF Report Exporter generates professional-quality PDF reports from any QUANTCLAW DATA module output. Reports include:

- **Professional styling** with branded headers and footers
- **Rich data visualization** with tables and charts (matplotlib)
- **Multiple report templates** (default, fundamental, technical, risk, complete)
- **Batch report generation** for multiple tickers
- **Customizable module selection** to include only what you need

## Installation

```bash
pip3 install --break-system-packages reportlab matplotlib
```

## Usage

### 1. Export PDF Report

Generate a PDF report for a single ticker:

```bash
# Full report with all modules
python cli.py export-pdf AAPL --modules all

# Selective modules
python cli.py export-pdf TSLA --modules earnings,technicals

# Use a specific template
python cli.py export-pdf MSFT --template fundamental

# Custom output path
python cli.py export-pdf GOOGL --modules all --output /tmp/google_report.pdf
```

### 2. Batch Report Generation

Generate reports for multiple tickers:

```bash
# Batch with default modules
python cli.py batch-report AAPL,MSFT,GOOGL

# Batch with selective modules
python cli.py batch-report AAPL,TSLA,NVDA --modules price,technicals,earnings

# Batch with specific template
python cli.py batch-report AAPL,MSFT,GOOGL --template risk
```

### 3. List Available Templates

View all available report templates:

```bash
python cli.py report-template list
```

## Templates

### Default
Standard report with core sections:
- Company profile
- Price data
- Technical analysis
- Earnings
- Dividends
- Analyst ratings

### Fundamental
Deep dive into fundamentals:
- Company profile
- Earnings
- Revenue quality
- Earnings quality
- Dividend health
- Executive compensation

### Technical
Chart-focused technical analysis:
- Price data
- Technical indicators
- Options chain
- Short interest

### Risk
Comprehensive risk analysis:
- Revenue quality
- Earnings quality
- Climate risk
- Activist prediction

### Complete
All available modules (comprehensive report)

## API Endpoints

### Export PDF

```
GET /api/v1/pdf-export?action=export&ticker=AAPL&modules=all&template=default
```

**Response:**
```json
{
  "status": "success",
  "ticker": "AAPL",
  "modules": ["profile", "price", "technicals", ...],
  "output_path": "/path/to/AAPL_report_20260225_120000.pdf",
  "timestamp": "2026-02-25T12:00:00.123456"
}
```

### Batch Export

```
GET /api/v1/pdf-export?action=batch&tickers=AAPL,MSFT,GOOGL&modules=all
```

**Response:**
```json
{
  "status": "success",
  "batch_count": 3,
  "results": [
    {
      "status": "success",
      "ticker": "AAPL",
      "modules": [...],
      "output_path": "...",
      "timestamp": "..."
    },
    ...
  ],
  "timestamp": "2026-02-25T12:00:00.123456"
}
```

### List Templates

```
GET /api/v1/pdf-export?action=templates
```

**Response:**
```json
{
  "status": "success",
  "templates": {
    "default": {
      "name": "Default",
      "description": "Standard report with all sections",
      "modules": ["profile", "price", ...]
    },
    ...
  },
  "count": 5
}
```

### Download PDF

```
GET /api/v1/pdf-export?action=download&file=AAPL_report_20260225_120000.pdf
```

Returns the PDF file with appropriate headers for download.

## Features

### Professional Styling

- **Branded colors**: QUANTCLAW green (#13C636) and blue (#00BFFF)
- **Clean typography**: Helvetica font family
- **Header/footer**: Company name, timestamp, page numbers
- **Responsive tables**: Auto-sized columns with alternating row colors

### Data Visualization

- **Tables**: Clean, professional tables with headers and color-coded rows
- **Charts**: Matplotlib integration for charts (future enhancement)
- **Formatting**: Smart handling of dictionaries, lists, and nested data

### Output Management

- **Automatic naming**: `TICKER_report_YYYYMMDD_HHMMSS.pdf`
- **Custom paths**: Specify your own output location
- **Batch processing**: Generate multiple reports in one command
- **Directory structure**: Reports saved to `data/reports/`

## Module Integration

The PDF exporter can pull data from any QUANTCLAW module:

- **Core data**: price, profile, technicals, options
- **Fundamentals**: earnings, dividends, ratings, revenue-quality
- **Risk**: earnings-quality, climate-risk, activist-predict
- **Alternative data**: exec-comp, buyback-analysis, 13f-changes
- **And more...**: Any module with JSON output

## Error Handling

- **Missing modules**: Continues with available modules, logs warnings
- **Data failures**: Graceful degradation, includes partial data
- **Timeout protection**: 120-second limit per report
- **File validation**: Prevents directory traversal attacks

## Storage

Reports are stored in:
```
/home/quant/apps/quantclaw-data/data/reports/
```

File naming convention:
```
TICKER_report_YYYYMMDD_HHMMSS.pdf
```

## Security

- **Path sanitization**: Prevents directory traversal
- **File type validation**: Only PDF files served
- **Size limits**: 10MB buffer limit for API responses
- **Error disclosure**: No sensitive path information in errors

## Performance

- **Single report**: ~5-30 seconds (depending on modules)
- **Batch reports**: Linear scaling with ticker count
- **Memory efficient**: Streams data, doesn't load all in memory
- **Caching**: Leverages existing module caching

## Future Enhancements

- **Email delivery**: Send reports via email
- **Chart generation**: Embed matplotlib charts in PDFs
- **Custom branding**: User-configurable colors/logos
- **Scheduled reports**: Cron-based automated report generation
- **PDF merging**: Combine multiple reports into one
- **Excel export**: Alternative format option

## Troubleshooting

### Missing Dependencies

```bash
Error: reportlab not installed. Run: pip install reportlab matplotlib
```

**Solution:**
```bash
pip3 install --break-system-packages reportlab matplotlib
```

### Module Not Found

```bash
Warning: Failed to fetch profile: Module profile failed: Error: Unknown command 'profile'
```

**Solution:** Use a valid module name from the available modules list. Check `cli.py` for available commands.

### Empty Reports

If a report generates but appears empty, check:
1. Module is implemented and returning data
2. Ticker symbol is valid
3. API/data sources are accessible

## Examples

### Complete Report for Apple

```bash
python cli.py export-pdf AAPL --template complete
```

### Risk Assessment Report

```bash
python cli.py export-pdf TSLA --template risk
```

### Technical Analysis for Multiple Stocks

```bash
python cli.py batch-report AAPL,TSLA,NVDA,AMD --template technical
```

### Custom Module Selection

```bash
python cli.py export-pdf MSFT --modules revenue-quality,earnings-quality,exec-comp
```

## Contributing

To add new modules to the PDF exporter:

1. Add module name to `module_commands` dict in `_fetch_module_data()`
2. Ensure module returns valid JSON
3. Test with `export-pdf TICKER --modules your-module`

## License

Part of QUANTCLAW DATA — Phase 79 (Infrastructure)
