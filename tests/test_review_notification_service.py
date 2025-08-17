"""Tests for review notification logging behavior."""

import sys
import types

import pytest
from flask import Flask

# Stub out ``mailjet_rest`` before importing the service module
mailjet_module = types.ModuleType("mailjet_rest")
client_module = types.ModuleType("mailjet_rest.client")


class ApiError(Exception):
    """Lightweight replacement for the real Mailjet ApiError."""


client_module.ApiError = ApiError
mailjet_module.client = client_module
sys.modules.setdefault("mailjet_rest", mailjet_module)
sys.modules.setdefault("mailjet_rest.client", client_module)

from extensions import db
import models
from models import ReviewEmailLog
import services.review_notification_service as rns


@pytest.fixture
def app():
    """Create a minimal Flask application with an in-memory database."""

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="test",
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def create_basic_review():
    """Create a review with the minimum required relations."""

    reviewer = models.Usuario(
        nome="Rev",
        cpf="000",
        email="rev@test",
        senha="pwd",
        formacao="X",
    )
    db.session.add(reviewer)
    db.session.commit()

    submission = models.Submission(title="Sub", code_hash="hash")
    db.session.add(submission)
    db.session.commit()

    review = models.Review(
        submission_id=submission.id, reviewer_id=reviewer.id, access_code="123"
    )
    db.session.add(review)
    db.session.commit()
    return review


def test_email_failure_persists_log_on_outer_rollback(app, monkeypatch):
    """An email failure is logged even if surrounding work is rolled back."""

    with app.app_context():
        review = create_basic_review()

        def fail_send(*args, **kwargs):
            raise ApiError("boom")

        monkeypatch.setattr(rns, "send_via_mailjet", fail_send)

        try:
            rns.notify_reviewer(review)
            # Another change that will be rolled back
            db.session.add(models.Submission(title="Other", code_hash="h2"))
            raise RuntimeError("outer failure")
        except RuntimeError:
            db.session.rollback()

        assert ReviewEmailLog.query.count() == 1

