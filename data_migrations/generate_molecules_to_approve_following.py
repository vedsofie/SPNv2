from chat_server import db
from models.forum import Forum
from models.follower import Follower
from models.user import User
from sqlalchemy import and_, or_


def create_approval_following():
    to_be_followers = [user for user in User.query.filter(or_(User.username=='fieldservice',
                                                                User.username=='cdrake')).all()]
    newMoleculeForum = Forum.query.filter_by(Subject='To Approve Molecules').first()
    if not newMoleculeForum:
        newMoleculeForum = Forum()
        newMoleculeForum.Color = '#cf79f2'
        if to_be_followers:
            newMoleculeForum.AccountID = to_be_followers[0].AccountID
        newMoleculeForum.Subject = "To Approve Molecules"

        db.session.add(newMoleculeForum)
        db.session.commit()

    for user in to_be_followers:
        follower = Follower.query.filter(and_(Follower.Type=='Forums',
                                              Follower.ParentID==newMoleculeForum.ForumID,
                                              Follower.UserID==user.UserID)).first()
        if not follower:
            follower = Follower(UserID=user.UserID,
                                Type='Forums',
                                ParentID=newMoleculeForum.ForumID)
            db.session.add(follower)
            db.session.commit()

if __name__ == "__main__":
    create_approval_following()

