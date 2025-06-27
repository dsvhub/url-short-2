from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Link
from app.forms import RegistrationForm, LoginForm, UpdateProfileForm, LinkForm, URLShortenerForm
import string
import random

import qrcode
from io import BytesIO
from flask import send_file

import subprocess
import os


main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/links_dashboard')
@login_required
def links_dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    pagination = Link.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=per_page)
    links = pagination.items
    return render_template('linkdash.html', links=links, pagination=pagination)


@main.route('/shorten', methods=['GET', 'POST'])
@login_required
def shorten_url():
    form = URLShortenerForm()
    shortened_url = None
    if form.validate_on_submit():
        original_url = form.original_url.data
        # Generate a unique short code
        short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        while Link.query.filter_by(short_code=short_code).first():
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        # Create and save the link
        link = Link(original_url=original_url, short_code=short_code, user_id=current_user.id)
        db.session.add(link)
        db.session.commit()
        # Construct the shortened URL
        shortened_url = url_for('main.redirect_to_url', short_code=short_code, _external=True)
        flash('URL shortened successfully!', 'success')
    return render_template('shorten.html', form=form, shortened_url=shortened_url)

@main.route('/<short_code>')
def redirect_to_url(short_code):
    link = Link.query.filter_by(short_code=short_code).first_or_404()
    link.clicks += 1
    db.session.commit()
    return redirect(link.original_url)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateProfileForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('edit_user.html', form=form, user=user)

@main.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Account deleted.', 'info')
    return redirect(url_for('main.register'))

@main.route('/create_link', methods=['GET', 'POST'])
@login_required
def create_link():
    form = LinkForm()
    if form.validate_on_submit():
        if Link.query.filter_by(short_code=form.short_code.data).first():
            flash('Short code already taken. Please choose another.', 'danger')
            return render_template('create_link.html', form=form)
        link = Link(original_url=form.original_url.data, short_code=form.short_code.data, user_id=current_user.id)
        db.session.add(link)
        db.session.commit()
        flash('Short link created.', 'success')
        return redirect(url_for('main.links_dashboard'))
    return render_template('create_link.html', form=form)

@main.route('/edit_link/<int:link_id>', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    link = Link.query.get_or_404(link_id)
    form = LinkForm(obj=link)
    if form.validate_on_submit():
        link.original_url = form.original_url.data
        link.short_code = form.short_code.data
        db.session.commit()
        flash('Link updated.', 'success')
        return redirect(url_for('main.links_dashboard'))
    return render_template('edit_link.html', form=form, link=link)

@main.route('/delete_link/<int:link_id>', methods=['POST'])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Link deleted.', 'info')
    return redirect(url_for('main.links_dashboard'))


@main.route('/qrcode/<short_code>')
@login_required
def generate_qrcode(short_code):
    link = Link.query.filter_by(short_code=short_code).first_or_404()
    short_url = url_for('main.redirect_to_url', short_code=short_code, _external=True)

    img = qrcode.make(short_url)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype='image/png', as_attachment=True, download_name=f"{short_code}_qrcode.png")

@main.route('/qrcode/view/<short_code>')
@login_required
def view_qrcode(short_code):
    link = Link.query.filter_by(short_code=short_code).first_or_404()
    short_url = url_for('main.redirect_to_url', short_code=short_code, _external=True)

    img = qrcode.make(short_url)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')  # No `as_attachment`

@main.route('/download_csv')
@login_required
def download_csv():
    import csv
    from io import StringIO
    links = Link.query.filter_by(user_id=current_user.id).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Original URL', 'Short Code', 'Clicks'])
    for link in links:
        writer.writerow([link.original_url, link.short_code, link.clicks])
    output = si.getvalue()
    return send_file(BytesIO(output.encode()), mimetype='text/csv', as_attachment=True, download_name='my_links.csv')


@main.route('/download_qrcodes_zip')
@login_required
def download_qrcodes_zip():
    from io import BytesIO
    from zipfile import ZipFile
    import qrcode

    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zf:
        links = Link.query.filter_by(user_id=current_user.id).all()
        for link in links:
            short_url = url_for('main.redirect_to_url', short_code=link.short_code, _external=True)
            img = qrcode.make(short_url)
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            zf.writestr(f"{link.short_code}.png", img_buffer.read())

    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='qrcodes.zip')

@main.route('/backup_db', methods=['POST'])
@login_required
def backup_db():
    from backup_db import upload_db
    asset_path = os.path.abspath('site.db')
    success = upload_db(asset_path)
    if success:
        flash('✅ Database backed up to GitHub.', 'success')
    else:
        flash('❌ Backup failed. Check logs.', 'danger')
    return redirect(url_for('main.links_dashboard'))


@main.route('/restore_db')
@login_required
def restore_db():
    try:
        subprocess.run(["python", "restore_db.py"], check=True)
        flash("Database restored from GitHub Releases.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Restore failed: {e}", "danger")
    return redirect(url_for('main.links_dashboard'))
