import json
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.services.verification_service import VerificationService
from app.models.verificationClaim import VerificationClaim
from app.utils.decorators import login_required
from app import db

verification_bp = Blueprint('verification', __name__)
verification_service = VerificationService()

@verification_bp.route("/post/<int:post_id>/verify", methods=["GET", "POST"])
@login_required
def verify_item(post_id):
    if request.method == "POST":
        try:
            verification_service.create_verification_claim(
                post_id, 
                session['user_id'],
                request.form,
                request.files
            )
            flash("Your verification claim has been submitted successfully.", "success")
            return redirect(url_for('posts.view_post', post_id=post_id))
        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for('verification.verify_item', post_id=post_id))
            
    post = verification_service.get_post(post_id)
    return render_template('verify_item.html', post=post)

@verification_bp.route("/post/<int:post_id>/claims")
@login_required
def view_claims(post_id):
    post = verification_service.get_post(post_id)
    
    if session.get("user_id") != post.user_id:
        flash("Access denied", "danger")
        return redirect(url_for("posts.view_post", post_id=post_id))
        
    claims = VerificationClaim.query.filter_by(post_id=post_id).all()
    claims_with_users = []
    for claim in claims:
        claim_data = json.loads(claim.proof_details)
        claims_with_users.append({
            'claim': claim,
            'user': claim.user,
            'proof_data': claim_data
        })
    
    return render_template("view_claims.html", post=post, claims=claims_with_users)

@verification_bp.route("/post/<int:post_id>/claim/<int:claim_id>/update", methods=["POST"])
@login_required
def update_claim_status(post_id, claim_id):
    post = verification_service.get_post(post_id)
    claim = VerificationClaim.query.get_or_404(claim_id)
    
    if session.get("user_id") != post.user_id:
        flash("Access denied", "danger")
        return redirect(url_for("posts.view_post", post_id=post_id))
    
    new_status = request.form.get("status")
    if new_status in ["approved", "rejected"]:
        claim.status = new_status
        if new_status == "approved":
            post.verification_status = "verified"
        db.session.commit()
        flash(f"Claim has been {new_status}", "success")
    
    return redirect(url_for("verification.view_claims", post_id=post_id))
