#!/usr/bin/env python3
# The above shebang (#!) operator tells Unix-like environments
# to run this file as a python3 script

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/order_schema'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)  


class Order_detail(db.Model):
    __tablename__ = 'order_detail'

    order_id = db.Column(db.Integer, primary_key=True)
    # order_item = db.relationship('Order_Item', backref='order', cascade='all, delete-orphan')
    cart_amt = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    payment_id = db.Column(db.Integer,nullable=False)
    shipping_id = db.Column(db.Integer,nullable=False)
    error_id = db.Column(db.Integer)
    status = db.Column(db.String(10), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    modified = db.Column(db.DateTime, nullable=False,
                         default=datetime.now, onupdate=datetime.now)

    def json(self):
        dto = {
            'order_id': self.order_id,
            'user_id': self.user_id,
            # 'order_item' : self.order_item,
            'cart_amt' : self.cart_amt,
            'payment_id' : self.payment_id,
            'shipping_id' : self.shipping_id,
            'error_id' : self.error_id,
            'status': self.status,
            'created': self.created,
            'modified': self.modified
        }

        dto['order_item'] = []
        for oi in self.order_item:
            dto['order_item'].append(oi.json())

        return dto


class Order_Item(db.Model):
    __tablename__ = 'order_item'

    item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.ForeignKey(
        'order_detail.order_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    # item_name= db.Column(db.String, nullable=False)
    # book_id = db.Column(db.String(13), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # order_id = db.Column(db.String(36), db.ForeignKey('order.order_id'), nullable=False)
    # order = db.relationship('Order', backref='order_item')
    order = db.relationship(
        'Order_detail', primaryjoin='Order_Item.order_id == Order_detail.order_id', backref='order_item')

    def json(self):
        return {'item_id': self.item_id, 'quantity': self.quantity, 'order_id': self.order_id}


@app.route("/order")
def get_all():
    orderlist = db.session.scalars(db.select(Order_detail)).all()
    if len(orderlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "orders": [order.json() for order in orderlist]
                }
            }
        )
    return jsonify(
        {~
            "code": 404,
            "message": "There are no orders."
        }
    ), 404


@app.route("/order/<string:order_id>")
def find_by_order_id(order_id):
    order = db.session.scalars(
        db.select(Order_detail).filter_by(order_id=order_id).limit(1)).first()
    if order:
        return jsonify(
            {
                "code": 200,
                "data": order.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "order_id": order_id
            },
            "message": "Order not found."
        }
    ), 404


@app.route("/order", methods=['POST'])
def create_order():
    user_id = request.json.get('user_id', None)
    order = Order_detail(user_id=user_id, status='NEW')

    cart_item = request.json.get('cart_item')
    for item in cart_item:
        order.order_item.append(Order_Item(
            book_id=item['book_id'], quantity=item['quantity']))

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the order. " + str(e)
            }
        ), 500
    
    print(json.dumps(order.json(), default=str)) # convert a JSON object to a string and print
    print()

    return jsonify(
        {
            "code": 201,
            "data": order.json()
        }
    ), 201


@app.route("/order/<string:order_id>", methods=['PUT'])
def update_order(order_id):
    try:
        order = db.session.scalars(
        db.select(Order_detail).filter_by(order_id=order_id).
        limit(1)).first()
        if not order:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "order_id": order_id
                    },
                    "message": "Order not found."
                }
            ), 404

        # update status
        data = request.get_json()
        if data['status']:
            order.status = data['status']
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": order.json()
                }
            ), 200
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "order_id": order_id
                },
                "message": "An error occurred while updating the order. " + str(e)
            }
        ), 500


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage orders ...")
    app.run(host='0.0.0.0', port=5001, debug=True)
