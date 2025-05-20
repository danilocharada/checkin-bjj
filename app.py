from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db
import datetime
import os
import json
from urllib.parse import unquote

# Inicializar o Firebase usando variável de ambiente FIREBASE_CREDENTIALS
firebase_cred_json = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_cred_json:
    raise Exception("Variável de ambiente FIREBASE_CREDENTIALS não encontrada!")

try:
    firebase_cred_dict = json.loads(firebase_cred_json)
except json.JSONDecodeError:
    raise Exception("Erro ao decodificar o JSON da variável FIREBASE_CREDENTIALS.")

cred = credentials.Certificate(firebase_cred_dict)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://checkin-bjj-default-rtdb.firebaseio.com/'  # Substitua pelo seu URL real se mudar
})

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def aluno():
    mensagem = None
    if request.method == "POST":
        nome = request.form["nome"]
        if nome:
            ref = db.reference("checkins")
            ref.push({
                "nome": nome.strip().lower(),
                "status": "pendente",
                "timestamp": datetime.datetime.now().isoformat()
            })
            mensagem = "Check-in enviado! Aguarde a confirmação do professor."
    return render_template("aluno.html", mensagem=mensagem)

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        senha = request.form["senha"]
        if senha == "010203":
            return redirect(url_for("professor"))
        else:
            erro = "Senha incorreta."
    return render_template("login.html", erro=erro)

@app.route("/professor")
def professor():
    checkins_ref = db.reference("checkins")
    checkins_pendentes = checkins_ref.order_by_child("status").equal_to("pendente").get() or {}
    historico_ref = db.reference("historico")
    historico = historico_ref.get() or {}
    return render_template("professor.html", checkins_pendentes=checkins_pendentes, historico=historico)

@app.route("/aceitar/<id>", methods=["POST"])
def aceitar(id):
    ref = db.reference(f"checkins/{id}")
    checkin = ref.get()
    if not checkin:
        return "Check-in não encontrado", 404

    nome = checkin.get("nome")
    if not nome:
        return "Nome inválido", 400

    nome_limpo = nome.strip().lower()
    historico_ref = db.reference(f"historico/{nome_limpo}")
    atual = historico_ref.get() or 0
    historico_ref.set(atual + 1)
    ref.delete()

    return redirect(url_for("professor"))

@app.route("/rejeitar/<id>", methods=["POST"])
def rejeitar(id):
    ref = db.reference(f"checkins/{id}")
    ref.delete()
    return redirect(url_for("professor"))

@app.route("/apagar/<path:nome>", methods=["POST"])
def apagar(nome):
    nome_decodificado = unquote(nome)
    db.reference(f"historico/{nome_decodificado}").delete()
    return redirect(url_for("professor"))

if __name__ == "__main__":
    app.run(debug=False)
