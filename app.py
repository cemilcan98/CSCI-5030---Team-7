from os import terminal_size
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from hunspell import Hunspell
import string
import sys
import random
from irishspell import irishspell
from GEC_python import predict
import nltk

app = Flask(__name__, template_folder="templates")

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

h = Hunspell()
s = irishspell()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form["submit_button"] == "submit":
            # check if text is empty or not
            if not request.form.get("text"):
                error = "Please provide a text to check"
                return render_template("index.html", error=error)
            session['text'] = request.form.get("text")
            session['given_text'] = session['text']
            # checking punctuation marks
            punc = '''!()-[]{};:"\,<>./?@#$%^&*_~'''
            for element in session['text']:
                if element in punc:
                    session['text'] = session['text'].replace(element, "")
            session['text'] = session['text'].lower()
            session['words'] = session['text'].split()
            session['misspelled'] = []

            if request.form.get("lang") == "English":
                for word in session['words']:
                    if h.spell(word) == True:
                        continue
                    session['misspelled'].append(word)
                # create suggestions from the dictionary
                session['suggestions'] = dict.fromkeys(session['misspelled'])
                for key in session['suggestions']:
                    session['suggestions'][key] = h.suggest(key)
                return render_template("/index.html", text=session['given_text'], misspelled=session['misspelled'], suggestions=session['suggestions'])
            elif request.form.get("lang") == "En_context":
                out = predict(session['text'])
                out2 = str(out)
                print("output is: ", out)
                print("output without brackets is: ", out2[2:-8])
                session['misspelled'].append(out2[2:-8])
                return render_template("/index.html", text=session['given_text'], misspelled=session['misspelled'], suggestions=session['suggestions'])
            elif request.form.get("lang") == "Irish":
                session['trigrams'] = list(nltk.ngrams(nltk.word_tokenize(session['text']), 3))
                s = irishspell()
                session['prob'] = {}

                for word in session['words']:
                    if s.spell(word) == True:
                        continue
                    session['misspelled'].append(word)
                for gram in session['trigrams']:
                    for key in session['misspelled']:
                        session['suggestions'][key] = s.suggest(key,5)
                        if key == gram[1]:
                            session['prob'][key] = s.gram(gram, key)
                for mis in session['misspelled']:
                    if mis not in session['prob'].keys():
                        session['prob'][mis] = session['suggestions'][mis]

                return render_template("/index.html", text=session['given_text'], misspelled=session['misspelled'], suggestions=session['prob'])

        elif request.form["submit_button"] == "clear":
            return render_template("/index.html")
        # if user uses the correct button, this function first checks if text is empty or not,
        # and then spells it
        elif request.form["submit_button"] == "correct":
            if not request.form.get("text"):
                error = "Please provide a text to check"
                return render_template("index.html", error=error)
            session['new_text'] = session['given_text']
            for word in session['misspelled']:
                if request.form.get(word) != None:
                    session['new_text'] = session['new_text'].replace(
                        word, request.form.get(word))
                else:
                    error = "Please select a correction for all misspelled words"
                    return render_template("/index.html", error=error, text=session['given_text'], misspelled=session['misspelled'], suggestions=session['suggestions'])
            return render_template("/index.html", text=session['given_text'], new_text=session['new_text'], misspelled=session['misspelled'], suggestions=session['suggestions'])
        # if user uses the example button, this function creates some correct and wrong sentences
        elif request.form["submit_button"] == "example":

            example_dict = {
                1: 'What can I do with this?',
                2: "As you can easily notice the second block of text looks more realistic.",
                3: "Sam is looking for a job.",
                4: "I need to buy some things from IKEA.",
                5: "I hope to visit Peru again in the future.",
                6: "David came to dinnner with us.",
                7: "Would you lika to travl with me?",
                8: "I love learnning!",
            }
            # this random function make a random number every time so we can use it to have a new sentence
            # every time user uses the example button
            rand_num = random.randint(1, len(example_dict))
            example_text = example_dict[rand_num]
            return render_template("/index.html", text=example_text)

    else:
        return render_template("/index.html")

if __name__ == "__main__":
    app.run()
    #text = "Dia duite is anim dom Omar"
