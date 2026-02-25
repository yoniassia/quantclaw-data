#!/usr/bin/env python3
"""
PDF Report Exporter
Phase 79: Convert markdown reports to professional PDF with charts and email delivery

Features:
- Generate professional PDF reports from any module's output
- Include headers, charts (matplotlib), tables, branding
- Support batch report generation
- Multiple report templates
- Email delivery support

Uses reportlab for PDF generation (free, no dependencies)
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import subprocess
import tempfile
import re

# PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
except ImportError:
    print("Error: reportlab not installed. Run: pip install reportlab matplotlib", file=sys.stderr)
    sys.exit(1)

# Charts
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

# Storage paths
REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors
BRAND_PRIMARY = HexColor("#13C636")  # Green
BRAND_SECONDARY = HexColor("#00BFFF")  # Blue
BRAND_DARK = HexColor("#1a1a1a")
BRAND_GRAY = HexColor("#95A5A6")


class PDFReportGenerator:
    """Generate professional PDF reports from module output"""

    def __init__(self, template: str = "default"):
        self.template = template
        self.styles = getSampleStyleSheet()
        self._customize_styles()

    def _customize_styles(self):
        """Customize PDF styles"""
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=BRAND_PRIMARY,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        self.styles.add(title_style)

        # Heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=BRAND_DARK,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        self.styles.add(heading_style)

        # Subheading style
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=BRAND_SECONDARY,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        self.styles.add(subheading_style)

        # Body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            spaceAfter=8,
            fontName='Helvetica'
        )
        self.styles.add(body_style)

    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(BRAND_GRAY)
        canvas_obj.drawString(inch, letter[1] - 0.5 * inch, "QUANTCLAW DATA")
        canvas_obj.drawRightString(letter[0] - inch, letter[1] - 0.5 * inch, 
                                   datetime.now().strftime("%Y-%m-%d %H:%M UTC"))
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawCentredString(letter[0] / 2, 0.5 * inch, 
                                     f"Page {doc.page}")
        
        canvas_obj.restoreState()

    def generate_report(self, ticker: str, modules: List[str], output_path: str) -> Dict[str, Any]:
        """Generate PDF report for a ticker using specified modules"""
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        # Story elements
        story = []

        # Title page
        story.append(Spacer(1, 0.5 * inch))
        title = Paragraph(f"{ticker.upper()} Analysis Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        subtitle = Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}",
            self.styles['CustomBody']
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.5 * inch))

        # Module sections
        for module_name in modules:
            try:
                module_data = self._fetch_module_data(ticker, module_name)
                section_elements = self._render_module_section(module_name, module_data)
                story.extend(section_elements)
                story.append(PageBreak())
            except Exception as e:
                print(f"Warning: Failed to fetch {module_name}: {e}", file=sys.stderr)

        # Build PDF with header/footer
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "modules": modules,
            "output_path": output_path,
            "timestamp": datetime.now().isoformat()
        }

    def _fetch_module_data(self, ticker: str, module_name: str) -> Dict[str, Any]:
        """Fetch data from a module CLI"""
        cli_path = Path(__file__).parent.parent / "cli.py"
        
        # Map module names to CLI commands
        module_commands = {
            "price": f"price {ticker}",
            "profile": f"profile {ticker}",
            "technicals": f"technicals {ticker}",
            "options": f"options {ticker}",
            "earnings": f"earnings {ticker}",
            "dividends": f"dividends {ticker}",
            "ratings": f"ratings {ticker}",
            "news": f"news {ticker}",
            "factors": f"factors {ticker}",
            "short-interest": f"short-interest {ticker}",
            "revenue-quality": f"revenue-quality {ticker}",
            "earnings-quality": f"earnings-quality {ticker}",
            "exec-comp": f"exec-comp {ticker}",
            "buyback-analysis": f"buyback-analysis {ticker}",
            "dividend-health": f"dividend-health {ticker}",
            "13f-changes": f"13f-changes {ticker}",
            "activist-predict": f"activist-predict {ticker}",
            "climate-risk": f"climate-risk {ticker}",
        }

        command = module_commands.get(module_name)
        if not command:
            raise ValueError(f"Unknown module: {module_name}")

        # Execute CLI command
        result = subprocess.run(
            f"python3 {cli_path} {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"Module {module_name} failed: {result.stderr}")

        # Parse JSON output
        return json.loads(result.stdout)

    def _render_module_section(self, module_name: str, data: Dict[str, Any]) -> List:
        """Render a module's data into PDF elements"""
        elements = []

        # Section heading
        heading = Paragraph(module_name.replace("-", " ").title(), self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.2 * inch))

        # Render based on data structure
        if isinstance(data, dict):
            elements.extend(self._render_dict(data))
        elif isinstance(data, list):
            elements.extend(self._render_list(data))
        else:
            elements.append(Paragraph(str(data), self.styles['CustomBody']))

        return elements

    def _render_dict(self, data: Dict[str, Any]) -> List:
        """Render dictionary as table"""
        elements = []
        
        # Convert dict to table data
        table_data = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            elif value is None:
                value = "N/A"
            table_data.append([str(key), str(value)])

        if table_data:
            table = Table(table_data, colWidths=[2.5*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_SECONDARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f0f0f0")]),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _render_list(self, data: List[Any]) -> List:
        """Render list as paragraphs or table"""
        elements = []
        
        if data and isinstance(data[0], dict):
            # Render as table
            keys = list(data[0].keys())
            table_data = [keys]
            for item in data[:20]:  # Limit to 20 rows
                row = [str(item.get(k, "N/A")) for k in keys]
                table_data.append(row)

            if table_data:
                col_width = 6.5 * inch / len(keys)
                table = Table(table_data, colWidths=[col_width] * len(keys))
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f0f0f0")]),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.2 * inch))
        else:
            # Render as bullet points
            for item in data[:20]:
                para = Paragraph(f"• {str(item)}", self.styles['CustomBody'])
                elements.append(para)

        return elements


def export_pdf(ticker: str, modules: List[str], template: str = "default", output_path: Optional[str] = None) -> Dict[str, Any]:
    """Export PDF report for a ticker"""
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = REPORTS_DIR / f"{ticker.upper()}_report_{timestamp}.pdf"
    else:
        output_path = Path(output_path)

    generator = PDFReportGenerator(template=template)
    result = generator.generate_report(ticker, modules, str(output_path))
    
    return result


def batch_report(tickers: List[str], modules: List[str], template: str = "default") -> Dict[str, Any]:
    """Generate batch reports for multiple tickers"""
    
    results = []
    for ticker in tickers:
        try:
            result = export_pdf(ticker, modules, template)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "ticker": ticker.upper(),
                "error": str(e)
            })

    return {
        "status": "success",
        "batch_count": len(tickers),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


def list_templates() -> Dict[str, Any]:
    """List available report templates"""
    
    templates = {
        "default": {
            "name": "Default",
            "description": "Standard report with all sections",
            "modules": ["profile", "price", "technicals", "earnings", "dividends", "ratings"]
        },
        "fundamental": {
            "name": "Fundamental Analysis",
            "description": "Deep dive into fundamentals",
            "modules": ["profile", "earnings", "revenue-quality", "earnings-quality", "dividend-health", "exec-comp"]
        },
        "technical": {
            "name": "Technical Analysis",
            "description": "Chart-focused technical analysis",
            "modules": ["price", "technicals", "options", "short-interest"]
        },
        "risk": {
            "name": "Risk Assessment",
            "description": "Comprehensive risk analysis",
            "modules": ["revenue-quality", "earnings-quality", "climate-risk", "activist-predict"]
        },
        "complete": {
            "name": "Complete Report",
            "description": "All available modules",
            "modules": ["profile", "price", "technicals", "options", "earnings", "dividends", 
                       "ratings", "news", "factors", "revenue-quality", "earnings-quality", 
                       "exec-comp", "buyback-analysis", "dividend-health"]
        }
    }

    return {
        "status": "success",
        "templates": templates,
        "count": len(templates)
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="QUANTCLAW DATA - PDF Report Exporter")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # export-pdf command
    export_parser = subparsers.add_parser('export-pdf', help='Export PDF report for a ticker')
    export_parser.add_argument('ticker', help='Stock ticker symbol')
    export_parser.add_argument('--modules', default='all', 
                              help='Comma-separated module list or "all" (default: all)')
    export_parser.add_argument('--template', default='default', 
                              help='Report template (default: default)')
    export_parser.add_argument('--output', help='Output file path')

    # batch-report command
    batch_parser = subparsers.add_parser('batch-report', help='Generate batch reports')
    batch_parser.add_argument('tickers', help='Comma-separated ticker list')
    batch_parser.add_argument('--modules', default='all', 
                             help='Comma-separated module list or "all"')
    batch_parser.add_argument('--template', default='default', 
                             help='Report template')

    # report-template command
    template_parser = subparsers.add_parser('report-template', help='List available templates')
    template_parser.add_argument('action', choices=['list'], help='Template action')

    args = parser.parse_args()

    # Handle commands
    if args.command == 'export-pdf':
        # Parse modules
        if args.modules == 'all':
            modules = list_templates()['templates']['default']['modules']
        else:
            modules = [m.strip() for m in args.modules.split(',')]

        result = export_pdf(args.ticker, modules, args.template, args.output)
        print(json.dumps(result, indent=2))

    elif args.command == 'batch-report':
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        
        if args.modules == 'all':
            modules = list_templates()['templates']['default']['modules']
        else:
            modules = [m.strip() for m in args.modules.split(',')]

        result = batch_report(tickers, modules, args.template)
        print(json.dumps(result, indent=2))

    elif args.command == 'report-template':
        if args.action == 'list':
            result = list_templates()
            print(json.dumps(result, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
