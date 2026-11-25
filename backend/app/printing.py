"""PDF generation API routes."""
from io import BytesIO

from flask import jsonify, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from xml.sax.saxutils import escape as xml_escape
from .validation import json_object


def register_print_routes(app, role_required):
    @app.route('/api/print-data', methods=['POST'])
    @role_required(['user', 'editor', 'admin', 'accountant'])
    def print_data():
        data = json_object()
        if data is None:
            return jsonify({'message': 'Print data must be an object'}), 400
        title = 'NEW WAY'
        subtitle = data.get('subtitle', '')
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        if not isinstance(subtitle, str) or len(subtitle) > 300 or not isinstance(headers, list) or not isinstance(rows, list) or len(headers) > 20 or len(rows) > 1000 or any(not isinstance(row, list) or len(row) > 20 for row in rows):
            return jsonify({'message': 'Invalid or oversized print data'}), 400

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontSize = 18
        title_style.fontName = 'Helvetica-Bold'
        title_paragraph = Paragraph(title, title_style)
        subtitle_paragraph = Paragraph(xml_escape(subtitle), styles['Heading2'])
        elements.append(title_paragraph)
        elements.append(subtitle_paragraph)

        safe_cell = lambda value: xml_escape(str(value)[:1000])
        table_data = [[safe_cell(cell) for cell in headers]] + [[safe_cell(cell) for cell in row] for row in rows]
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, download_name='data_summary.pdf', as_attachment=True)

