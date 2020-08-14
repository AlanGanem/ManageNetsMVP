from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func, exc
import pandas as pd


@login.user_loader
def load_user(id):
    try:
        return User.query.get(int(id))
    except exc.OperationalError:
        return None

def as_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def edit_sets(new_ids, old_ids):
    assert new_ids.__class__ == set
    assert old_ids.__class__ == set
    to_add = new_ids - old_ids
    to_delete = inputs_ids - new_inputs_ids
    to_keep = new_inputs_ids & inputs_ids
    return {'to_add':to_add,'to_delete':to_delete,'to_keep':to_keep}

class BaseColumns:
    name = db.Column(db.String(32))
    description = db.Column(db.String(4096))
    creation_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    deletion_date = db.Column(db.DateTime, index=True, default=None)
    created_by = db.Column(db.Integer)
    owner = db.Column(db.Integer)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    #user_id = db.Column(db.Integer)
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#class ProductStandard(db.Model, BaseColumns):
#    '''parent abstract class for products'''
#    pass

#class ProcessStandard(db.Model, BaseColumns):
#    '''parent abstract class for processes'''
#    pass

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post {self.body}>'

class Process(db.Model, BaseColumns):
    id = db.Column(db.Integer, primary_key = True)
    process_id = db.Column(db.Integer)
    parent_process_id = db.Column(db.Integer)
    products = db.relationship('Product', backref='process', lazy='dynamic')
    is_abstract = db.Column(db.Boolean, default = False)

    def __repr__(self):
        return f'<Process {self.description}>'

class Link(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    process_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    link_type = db.Column(db.String)
    creation_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    deletion_date = db.Column(db.DateTime, index=True, default=None)

    def __repr__(self):
        return f'<Link {(self.process_id,self.product_id)}>'

class Product(db.Model, BaseColumns):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    def __reppr__(self):
        return f'<Product {self.description}>'