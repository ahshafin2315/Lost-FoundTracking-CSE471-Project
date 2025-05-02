import json
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.services.verification_service import VerificationService
from app.services.notification_service import NotificationService
from app.utils.decorators import login_required

verification_bp = Blueprint('verification', __name__)
verification_service = VerificationService()
notification_service = NotificationService()

@verification_bp.route("/post/<int:post_id>/verify", methods=["GET", "POST"])
@login_required
def verify_item(post_id):
    if request.method == "POST":
        try:
            claim = verification_service.create_verification_claim(
                post_id,
                session['user_id'],
                request.form,
                request.files
            )
            post = verification_service.get_post(post_id)

            # Notify post owner about new claim
            notification_service.create_verification_notification(
                post.user_id,
                f"New verification claim received for your item '{post.item_name}'",
                url_for('verification.view_claims', post_id=post_id)
            )

            flash("Your verification claim has been submitted successfully.", "success")
            return redirect(url_for('posts.view_post', post_id=post_id))
        except ValueError as e:
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

    claims = verification_service.get_post_claims(post_id)
    return render_template("view_claims.html", post=post, claims=claims)

@verification_bp.route("/post/<int:post_id>/claim/<int:claim_id>/update", methods=["POST"])
@login_required
def update_claim_status(post_id, claim_id):
    post = verification_service.get_post(post_id)
    if session.get("user_id") != post.user_id:
        flash("Access denied", "danger")
        return redirect(url_for("posts.view_post", post_id=post_id))

    new_status = request.form.get("status")
    if new_status in ["approved", "rejected"]:
        success = verification_service.update_claim_status(claim_id, post_id, new_status)
        if success:
            flash(f"Claim has been {new_status}", "success")
        else:
            flash("Error updating claim status", "danger")

    return redirect(url_for("verification.view_claims", post_id=post_id))

@verification_bp.route('/approve/<int:claim_id>', methods=['POST'])
@login_required
def approve_claim(claim_id):
    try:
        claim_data = verification_service.approve_claim(claim_id, session['user_id'])
        if claim_data:
            notification_service.create_chat_enabled_notifications(
                claim_data['claim_user_id'],
                claim_data['post_user_id'],
                claim_data['post_id'],
                claim_data['post_name']
            )
            flash('Claim has been approved successfully.', 'success')
            return redirect(url_for('posts.view_post', post_id=claim_data['post_id']))

        flash('Error approving claim', 'danger')
        return redirect(url_for('posts.view_post', post_id=claim_data['post_id']))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('dashboard.dashboard'))
