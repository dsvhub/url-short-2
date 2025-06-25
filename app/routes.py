from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Link
from app.forms import RegistrationForm, LoginForm, UpdateProfileForm, LinkForm, URLShortenerForm
import string
import random

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/links')
@login_required
def links_dashboard():
    user_links = Link.query.filter_by(user_id=current_user.id).all()
    return render_template('linkdash.html', links=user_links)

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
    return redirect(link.original_url)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
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
        if user and check_password_hash(user.password, form.password.data):
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