# from flask import Flask, redirect, render_template, url_for
from crypt import methods
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
from nltk.corpus import wordnet
import nltk
from flask import Flask, request, render_template, url_for, redirect, jsonify
from firebase_admin import credentials, firestore, initialize_app
import requests
app = Flask(__name__)

cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
todo_ref = db.collection('todos')
BASE = "http://127.0.0.1:5000/"
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')
# nltk.download('omw-1.4')
# Lemmatize with POS Tag
# Init the Wordnet Lemmatizer
lemmatizer = WordNetLemmatizer()


def get_wordnet_pos(word):
    # Map POS tag to first character lemmatize() accepts
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)


@app.route("/")
def home():
    return render_template("form.html")


@app.route("/learn", methods=['GET', 'POST'])
def lear():
    return render_template("index.html")


@app.route('/res', methods=['POST'])
def my_form_post():
    text = request.form['text']

    # Init Lemmatizer
    lemmatizer = WordNetLemmatizer()

    # Lemmatize a Sentence with the appropriate POS tag
    sentence = text
    dict_keywords = {"class": 0, "variable": 0, "setup": 0,
                     "object": 0, "function": 0, "comment": 0}

    sentence_list = [lemmatizer.lemmatize(
        w, get_wordnet_pos(w)) for w in nltk.word_tokenize(sentence)]
    print(sentence_list)

    # for word in sentence_list:
    #     if word in dict_keywords:
    #         dict_keywords[word] = dict_keywords[word] + 1

    for word in sentence_list:
        for key in dict_keywords:
            if fuzz.ratio(word, key) > 80:
                dict_keywords[key] = dict_keywords[key] + 1

    print(dict_keywords)

    words = []
    for key in dict_keywords:
        if dict_keywords[key] > 0:
            words.append(key)

    print(words)

    return "Your topic request is being processed..."


@app.route('/callAdd', methods=['GET'])
def callAdd():
    return render_template("add.html")


@app.route('/addByPost', methods=['POST'])
def addByPost():
    id = request.form.get('id')
    title = request.form.get('title')
    response = requests.post(
        BASE + "add", json={'id': id, 'title': title})
    response.raise_for_status()  # raises exception when not a 2xx response
    if response.status_code != 204:
        return response.json()

    return False


@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')
        if todo_id:
            todo = todo_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/callDelete', methods=['GET'])
def callDelete():
    return render_template("delete.html")


@app.route('/deleteByPost', methods=['POST'])
def deleteByPost():
    id = request.form.get('id')
    response = requests.delete(
        BASE + f"delete?id={id}")
    response.raise_for_status()  # raises exception when not a 2xx response
    if response.status_code != 204:
        return response.json()

    return False


@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


# @app.route("/<name>")
# def user(name):
#     return f"Hello {name}!"


if __name__ == "__main__":
    app.run()
