import json
from app.models.verificationClaim import VerificationClaim
from app.repositories.post_repository import PostRepository
from app.utils.image_utils import save_image
from app import db

class VerificationService:
    def __init__(self):
        self.post_repository = PostRepository()

    def get_post(self, post_id):
        return self.post_repository.get_by_id(post_id)

    def create_verification_claim(self, post_id, user_id, form_data, files):
        # Check for existing claim
        existing_claim = VerificationClaim.query.filter_by(
            post_id=post_id,
            user_id=user_id
        ).first()
        
        if existing_claim:
            raise ValueError("You have already submitted a claim for this item")

        proof_files = []
        if files:
            for file in files.getlist('proof_files'):
                if file.filename:
                    filename = save_image(file)
                    if filename:
                        proof_files.append(filename)

        claim = VerificationClaim(
            post_id=post_id,
            user_id=user_id,
            proof_details=json.dumps({
                'lost_location': form_data.get('lost_location'),
                'lost_date': form_data.get('lost_date'),
                'unique_identifier': form_data.get('unique_identifier'),
                'additional_proof': form_data.get('additional_proof'),
                'proof_files': proof_files
            })
        )
        
        db.session.add(claim)
        db.session.commit()
        return claim
