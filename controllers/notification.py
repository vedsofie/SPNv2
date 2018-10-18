from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, Response
from sqlalchemy import and_, or_
from models.user import User, db
from models.notification import Notification
from models.comment import Comment
from models.follower import Follower
import email_sender
import json

notificationcontroller = Blueprint("notificationcontroller", __name__, url_prefix="/notification")

@notificationcontroller.route("/", methods=["GET"])
def my_notifications():
    notes = Notification.query.all()
    resp = [note.to_hash for note in notes]
    return Response(json.dumps(resp), headers={"Content-Type": "application/json"})


@notificationcontroller.route("/<int:following_id>/", methods=["DELETE"])
def acknowledge_notifications(following_id):
    notifications = Notification.query.filter(Notification.FollowerID==following_id).all()
    for note in notifications:
        db.session.delete(note)
    db.session.commit()
    return Response("deleted", 204)