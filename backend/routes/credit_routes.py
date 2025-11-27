from flask import Blueprint, request, jsonify
from backend.models.credit import Credit
from backend.services.credit_service import CreditService

credit_bp = Blueprint('credit', __name__)
credit_service = CreditService()

@credit_bp.route("/credits/", methods=["POST"])
def create_credit():
    try:
        data = request.get_json()
        credit = Credit(data['amount'], data['interest_rate'])
        return jsonify(credit_service.create_credit(credit)), 201
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@credit_bp.route("/credits/<int:credit_id>", methods=["GET"])
def get_credit(credit_id):
    credit = credit_service.get_credit(credit_id)
    if credit is None:
        return jsonify({"detail": "Credit not found"}), 404
    return jsonify(credit)

@credit_bp.route("/credits/<int:credit_id>", methods=["PUT"])
def update_credit(credit_id):
    try:
        data = request.get_json()
        credit = Credit(data['amount'], data['interest_rate'])
        return jsonify(credit_service.update_credit(credit_id, credit))
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@credit_bp.route("/credits/<int:credit_id>", methods=["DELETE"])
def delete_credit(credit_id):
    success = credit_service.delete_credit(credit_id)
    if not success:
        return jsonify({"detail": "Credit not found"}), 404
    return jsonify({"detail": "Credit deleted successfully"})