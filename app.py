import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError

messages_list = []
banned_words = ["dinde", "en", "allemand"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(280), nullable=False)


class MessageSchema(Schema):
    message = fields.Str(required=True)
    is_sponsored = fields.Bool(required=True)

    def censor(self, message) -> str:
        censored_message = message
        for word in banned_words:
            censored_message = censored_message.replace(word, "****")
        if message != censored_message:
            save_msg_to_db(message)
        return censored_message

def save_msg_to_db(msg: str) -> None:
    message_record = Message(message=msg)
    db.session.add(message_record)
    db.session.commit()
    
message_schema = MessageSchema()

with app.app_context():
    if not os.path.exists("./messages.db"):
        db.create_all()

@app.route('/messages', methods=['POST'])
def create_item():
    try:
        new_message = message_schema.load(request.get_json())
        new_message["message"] = message_schema.censor(new_message["message"])
        if new_message["is_sponsored"]:
            messages_list.insert(0, new_message)
        else:
            messages_list.append(new_message)
        msg = Message(message=new_message["message"])
        db.session.add(msg)
        db.session.commit()
        return jsonify(new_message), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

if __name__ == '__main__':
    app.run(debug=True)
