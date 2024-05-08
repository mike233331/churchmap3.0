import os, secrets
from reader import app, db
from reader.models import Church
from flask import render_template, send_from_directory, request, flash, url_for, redirect, jsonify
from PIL import Image
from reader.forms import ChurchForm, UpdateChurch
from sqlalchemy.exc import IntegrityError

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    churchs = Church.query.order_by(Church.created_at.desc()).paginate(page=page, per_page=4)
    return render_template('index.html', churchs=churchs)

@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)    

@app.route('/<int:church_id>/')
def church(church_id):
    church = Church.query.get_or_404(church_id)
    return render_template('church.html', church=church)

@app.route('/countries/')
def countries():
    page = request.args.get('page', 1, type=int)
    churchs = Church.query.filter(Church.genre == 'триллер').paginate(page=page, per_page=4)
    return render_template('countries.html', churchs=churchs)

@app.route('/best/')
def best():
    page = request.args.get('page', 1, type=int)
    churchs = Church.query.filter(Church.rating > 4).paginate(page=page, per_page=4)
    return render_template('best.html', churchs=churchs)

@app.route('/russia/')
def russia():
    page = request.args.get('page', 1, type=int)
    churchs = Church.query.filter(Church.genre == 'триллер').paginate(page=page, per_page=4)
    return render_template('russia.html', churchs=churchs)

def save_picture(cover):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(cover.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)

    output_size = (220, 340)
    i = Image.open(cover)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/create/', methods=('GET', 'POST'))
def create():
    form = ChurchForm()
    if form.validate_on_submit():
        if form.cover.data:
            cover = save_picture(form.cover.data)
        else:
            cover ='default.jpg'   
        title = form.title.data
        author = form.author.data
        genre = form.genre.data
        rating = int(form.rating.data)
        description = form.description.data
        notes = form.notes.data
        church = Church(title=title,
            author=author,
            genre=genre,
            rating=rating,
            cover=cover,
            description=description,
            notes=notes)
        db.session.add(church)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('create.html', form=form)

@app.route('/<int:church_id>/edit/', methods=('GET', 'POST'))
def edit(church_id):
    church = Church.query.get_or_404(church_id)
    form = UpdateChurch()
    if form.validate_on_submit():
        if form.cover.data:
            cover = save_picture(form.cover.data)
        else:
            cover = church.cover
        church.title = form.title.data
        church.author = form.author.data
        church.genre = form.genre.data
        church.rating = int(form.rating.data)
        church.description = form.description.data
        church.notes = form.notes.data
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Произошла ошибка: такая книга уже есть в базе', 'error')
            return render_template('edit.html', form=form)
      
            
    elif request.method == 'GET':
        form.title.data = church.title
        form.author.data = church.author
        form.genre.data = church.genre
        form.rating.data = church.rating
        form.cover.data = church.cover
        form.description.data = church.description
        form.notes.data = church.notes

    return render_template('edit.html', form=form)      

@app.post('/<int:church_id>/delete/')
def delete(church_id):
    church = Church.query.get_or_404(church_id)
    db.session.delete(church)
    db.session.commit()
    return redirect(url_for('index'))    

@app.route('/export/')
def data():
  data = Church.query.all()
  return jsonify(data)  
