"""Financial year archive and restore APIs."""
from datetime import date

from flask import jsonify, request

from . import db
from .audit import record_audit_event
from .models import Challan, Invoice, Purchase, WastePlate


def register_archive_routes(app, role_required):
    def _fy_date_range(fy):
        """Return the date range for a four-digit financial year."""
        fy_start_year = 2000 + int(fy[:2])
        return date(fy_start_year, 4, 1), date(fy_start_year + 1, 3, 31)

    @app.route('/api/archive/years', methods=['GET'])
    @role_required(['admin'])
    def get_archive_years():
        """Return all distinct financial years and whether they are archived."""
        challan_years = db.session.query(Challan.financial_year).filter(
            Challan.financial_year.isnot(None)
        ).distinct().all()
        invoice_years = db.session.query(Invoice.financial_year).distinct().all()

        all_years = sorted(set(
            [r[0] for r in challan_years if r[0]] +
            [r[0] for r in invoice_years if r[0]]
        ))

        result = []
        for fy in all_years:
            challan_count = Challan.query.filter_by(financial_year=fy).count()
            archived_count = Challan.query.filter_by(financial_year=fy, is_archived=True).count()
            invoice_count = Invoice.query.filter_by(financial_year=fy).count()
            archived_invoices = Invoice.query.filter_by(financial_year=fy, is_archived=True).count()

            start, end = _fy_date_range(fy)
            purchase_count = Purchase.query.filter(Purchase.date.between(start, end)).count()
            waste_count = WastePlate.query.filter(WastePlate.waste_date.between(start, end)).count()

            result.append({
                "financial_year": fy,
                "challans": challan_count,
                "archived_challans": archived_count,
                "invoices": invoice_count,
                "archived_invoices": archived_invoices,
                "purchases": purchase_count,
                "waste_plates": waste_count,
                "is_archived": archived_count == challan_count and archived_invoices == invoice_count
            })

        return jsonify(result), 200

    @app.route('/api/archive/<string:fy>', methods=['POST'])
    @role_required(['admin'])
    def archive_financial_year(fy):
        """Archive all records belonging to a financial year."""
        if len(fy) != 4 or not fy.isdigit():
            return jsonify({"error": "Invalid financial year format. Use 4-digit string like '2526'."}), 400

        start, end = _fy_date_range(fy)

        # Check for challans that have no associated invoice yet (un-invoiced)
        # A challan is considered invoiced if its challan_code appears in any invoice's challan_references
        all_challans_in_fy = Challan.query.filter_by(financial_year=fy).all()
        all_invoices = Invoice.query.all()
        invoiced_refs = set()
        for inv in all_invoices:
            if inv.challan_references:
                for ref in inv.challan_references.split(','):
                    invoiced_refs.add(ref.strip())

        uninvoiced = []
        for ch in all_challans_in_fy:
            seq_str = str(ch.challan_sequence) if ch.challan_sequence else None
            if seq_str and seq_str not in invoiced_refs:
                uninvoiced.append(ch.challan_code)

        force = request.args.get('force', 'false').lower() == 'true'
        if uninvoiced and not force:
            return jsonify({
                "warning": f"{len(uninvoiced)} challan(s) in FY {fy} appear to have no invoice yet.",
                "uninvoiced_challans": uninvoiced,
                "hint": "Add ?force=true to archive anyway, or generate invoices first."
            }), 409

        challan_updated = Challan.query.filter_by(financial_year=fy).update({"is_archived": True})
        invoice_updated = Invoice.query.filter_by(financial_year=fy).update({"is_archived": True})
        purchase_updated = Purchase.query.filter(
            Purchase.date.between(start, end)
        ).update({"is_archived": True})
        waste_updated = WastePlate.query.filter(
            WastePlate.waste_date.between(start, end)
        ).update({"is_archived": True})

        record_audit_event('financial_year.archived', 'financial_year', fy)
        db.session.commit()
        return jsonify({
            "message": f"Financial year {fy} archived successfully.",
            "challans_archived": challan_updated,
            "invoices_archived": invoice_updated,
            "purchases_archived": purchase_updated,
            "waste_plates_archived": waste_updated
        }), 200

    @app.route('/api/archive/<string:fy>/restore', methods=['POST'])
    @role_required(['admin'])
    def restore_financial_year(fy):
        """Restore all archived records for a financial year."""
        if len(fy) != 4 or not fy.isdigit():
            return jsonify({"error": "Invalid financial year format. Use 4-digit string like '2526'."}), 400

        start, end = _fy_date_range(fy)

        challan_updated = Challan.query.filter_by(financial_year=fy).update({"is_archived": False})
        invoice_updated = Invoice.query.filter_by(financial_year=fy).update({"is_archived": False})
        purchase_updated = Purchase.query.filter(
            Purchase.date.between(start, end)
        ).update({"is_archived": False})
        waste_updated = WastePlate.query.filter(
            WastePlate.waste_date.between(start, end)
        ).update({"is_archived": False})

        record_audit_event('financial_year.restored', 'financial_year', fy)
        db.session.commit()
        return jsonify({
            "message": f"Financial year {fy} restored successfully.",
            "challans_restored": challan_updated,
            "invoices_restored": invoice_updated,
            "purchases_restored": purchase_updated,
            "waste_plates_restored": waste_updated
        }), 200

