from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Professeur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    matiere = db.Column(db.String(100), nullable=False)
    filiere = db.Column(db.String(100), nullable=False)
    seances = db.relationship('Seance', backref='professeur', lazy=True)

    @property
    def total_heures(self):
        total = sum((seance.heure_fin - seance.heure_debut).seconds / 3600 for seance in self.seances)
        return total


class Seance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professeur_id = db.Column(db.Integer, db.ForeignKey('professeur.id'), nullable=False)
    filiere = db.Column(db.String(100), nullable=False)
    matiere = db.Column(db.String(100), nullable=False)
    site = db.Column(db.String(100), nullable=False)
    heure_debut = db.Column(db.DateTime, nullable=False)
    heure_fin = db.Column(db.DateTime, nullable=False)

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_seance_form')
def add_seance_form():
    return render_template('add_seance_form.html')

@app.route('/seances')
def seances():
    site = request.args.get('site')
    if site:
        seances = Seance.query.filter_by(site=site).all()
    else:
        seances = Seance.query.all()
    sites = ["ESGIS Avédji", "ESGIS Adjidogome", "ESGIS Kodjeviakopé"]
    return render_template('seances.html', seances=seances, sites=sites)

@app.route('/professeurs')
def professeurs():
    professeurs = Professeur.query.all()
    return render_template('professeurs.html', professeurs=professeurs)

@app.route('/add_seance', methods=['POST'])
def add_seance():
    nom = request.form['nom']
    prenom = request.form['prenom']
    site = request.form['site']
    matiere = request.form['matiere']
    filiere = request.form['filiere']
    date = request.form['date']
    heure_debut = request.form['heure_debut']
    heure_fin = request.form['heure_fin']

    # Combiner la date et l'heure pour créer des objets datetime
    heure_debut = datetime.strptime(f"{date} {heure_debut}", '%Y-%m-%d %H:%M:%S')
    heure_fin = datetime.strptime(f"{date} {heure_fin}", '%Y-%m-%d %H:%M:%S')
    
    professeur = Professeur.query.filter_by(nom=nom, prenom=prenom).first()
    if not professeur:
        professeur = Professeur(nom=nom, prenom=prenom, matiere=matiere, filiere=filiere)
        db.session.add(professeur)
        db.session.commit()
    
    nouvelle_seance = Seance(
        professeur_id=professeur.id,
        filiere=filiere,
        matiere=matiere,
        site=site,
        heure_debut=heure_debut,
        heure_fin=heure_fin
    )
    db.session.add(nouvelle_seance)
    db.session.commit()
    return redirect('/seances')


@app.route('/edit_seance/<int:id>', methods=['GET', 'POST'])
def edit_seance(id):
    seance = Seance.query.get_or_404(id)
    if request.method == 'POST':
        seance.professeur.nom = request.form['nom']
        seance.professeur.prenom = request.form['prenom']
        seance.site = request.form['site']
        seance.matiere = request.form['matiere']
        seance.filiere = request.form['filiere']
        date = request.form['date']
        heure_debut = request.form['heure_debut']
        heure_fin = request.form['heure_fin']
        seance.heure_debut = datetime.strptime(f"{date} {heure_debut}", '%Y-%m-%d %H:%M:%S')
        seance.heure_fin = datetime.strptime(f"{date} {heure_fin}", '%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return redirect('/seances')
    else:
        return render_template('edit_seance.html', seance=seance)


@app.route('/delete_seance/<int:id>')
def delete_seance(id):
    seance = Seance.query.get_or_404(id)
    db.session.delete(seance)
    db.session.commit()
    return redirect('/seances')

@app.route('/search_seance')
def search_seance():
    query = request.args.get('query')
    seances = Seance.query.join(Professeur).filter(
        or_(
            Professeur.nom.ilike(f'%{query}%'),
            Professeur.prenom.ilike(f'%{query}%'),
            Seance.heure_debut.ilike(f'%{query}%'),
            Seance.site.ilike(f'%{query}%'),
            Seance.matiere.ilike(f'%{query}%'),
            Seance.filiere.ilike(f'%{query}%')
        )
    ).all()
    sites = ["ESGIS Avédji", "ESGIS Adjidogome", "ESGIS Kodjeviakopé"]
    return render_template('seances.html', seances=seances, sites=sites)


@app.route('/edit_professeur/<int:id>', methods=['GET', 'POST'])
def edit_professeur(id):
    professeur = Professeur.query.get_or_404(id)
    if request.method == 'POST':
        professeur.nom = request.form['nom']
        professeur.prenom = request.form['prenom']
        professeur.matiere = request.form['matiere']
        professeur.filiere = request.form['filiere']
        db.session.commit()
        return redirect('/professeurs')
    else:
        return render_template('edit_professeur.html', professeur=professeur)

@app.route('/delete_professeur/<int:id>')
def delete_professeur(id):
    professeur = Professeur.query.get_or_404(id)
    db.session.delete(professeur)
    db.session.commit()
    return redirect('/professeurs')


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Désactiver les mises à jour SSL/TLS en mode développement
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True)
