import datetime
import urllib
import time
import json

from flask import request, render_template, flash, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_

from app.queries import Inputer, query_active_process_links, query_active_process, query_active_product,\
    query_user_asset, query_all_active_products, query_all_active_processes, query_active_product_links,\
    query_deprecate_product, query_deprecate_process
from app.models import User, Process, Product, Link, as_dict
from app_extensions import pandas_extensions
from app.forms import LoginForm, UploadForm, RegistrationForm,\
    RegisterProcessForm, IterativeAddProductForm, CreateProductForm, EditProcessForm,EditProductForm
from app import app, db

#TODO: include abstrat(standard) processes and products
#TODO: make pop up for deletion form

def autenticate_owner(route,element):
    if element.owner != current_user.id:
        raise AssertionError('Permission denied')
    else:
        return route

@app.route('/')
@app.route('/index')
def index():
    if not current_user.is_anonymous:
        return render_template('index.html', title='Home')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember = form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or (url_parse(next_page).netloc != ''):
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        form.file.data.save('uploads/' + filename)
        global FILE_PATH
        FILE_PATH = 'uploads/' + filename
        return redirect(url_for('upload'))

    return render_template('upload.html', form=form)


@app.route('/register', methods = ['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        print('VALIDATED REGISTER')
        user = User(username = form.username.data.lower(), email = form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a register user!')
        return redirect(url_for('login'))
    print('NOT VALIDATED')
    return render_template('register.html', title = 'Register', form = form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username = username).first_or_404()
    posts = [
        {'author':user,'body':'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user = user, posts = posts)

@app.route('/user/create_process', methods = ['GET','POST'])
@login_required
def create_process():
    form = RegisterProcessForm()
    if form.validate_on_submit():
        process_id = Inputer.new_process(
            current_user.id,
            name = form.name.data,
            description = form.description.data
        )
        flash(f'Process "{form.name.data}" created with ID {process_id}')
        return redirect(url_for('create_process'))

    return render_template('create_process.html', form = form)

@app.route('/user/my_processes', methods = ['GET','POST'])
@login_required
def my_processes():
    processes = query_user_asset(user_id=session['_user_id'], asset_type='process')
    processes = [json.loads(json.dumps(i)) for i in processes]
    return render_template('my_processes.html', processes = processes)

@app.route('/user/my_products', methods = ['GET','POST'])
@login_required
def my_products():
    products = query_user_asset(user_id=session['_user_id'], asset_type='product')
    products = [json.loads(json.dumps(i)) for i in products]
    return render_template('my_products.html', products = products)


@app.route('/user/product/<product_id>', methods = ['GET','POST'])
@login_required
def product(product_id):
    product_obj = query_active_product(product_id)[0]
    input_to_process = query_active_product_links(product_id, 'input_to')
    output_of_process = query_active_product_links(product_id, 'output_of')
    product_dict = {
        'Product ID': product_obj['id'],
        'Product Name': product_obj['name'],
        'Product Description': product_obj['description'],
        'Product Owner': product_obj['owner'],
        'Product Description':product_obj['description'],
        'Created by': product_obj['created_by'],
        'Output of': output_of_process,
        'Input to': input_to_process,
    }

    return render_template('product.html', product=json.loads(json.dumps(product_dict)))

@app.route('/user/process/<process_id>', methods = ['GET','POST'])
@login_required
def process(process_id):
    process_obj = query_active_process(process_id)[0]
    inputs = query_active_process_links(process_id, 'input_to')
    outputs = query_active_process_links(process_id, 'output_of')
    process_dict = {
        'Process ID':process_obj['id'],
        'Process Name':process_obj['name'],
        'Process Description': process_obj['description'],
        'Process Owner':process_obj['owner'],
        'Created by':process_obj['created_by'],
        'Outputs': outputs,
        'Inputs': inputs,
    }
    return render_template('process.html', process = process_dict)


@app.route('/user/edit_process/<process_id>', methods = ['GET','POST'])
@login_required
def edit_process_info(process_id):
    process_obj = Process.query.filter_by(process_id=process_id).first_or_404()
    form = EditProcessForm(obj=process_obj)

    if request.method == 'POST':
        # edit info
        if request.form['form_name'] == 'Edit Links':
            return redirect(url_for('edit_process_links', process_id = process_id, state_str = 'init'))
        if request.form['form_name'] == 'save_changes':
            Inputer.edit_process_info(
                process_id,
                requester = session['_user_id'],
                name = request.form['name'],
                description = request.form['description'],
                owner = request.form['owner'],
                created_by = session['_user_id']
            )
            flash('New info saved')
            return redirect(url_for('my_processes'))

    return render_template('edit_process_info.html', form = form, process_id = process_id)

@app.route('/user/edit_product/<product_id>', methods = ['GET','POST'])
@login_required
def edit_product_info(product_id):
    product_obj = Product.query.filter_by(product_id=product_id).first_or_404()
    flash(product_obj)
    form = EditProductForm(obj=product_obj)

    if request.method == 'POST':
        # edit info
        if request.form['form_name'] == 'save_changes':
            Inputer.edit_product_info(product_id,requester, **new_attributes)

    return render_template('edit_product_info.html', form = form, product_id = product_id)

@app.route('/user/edit_process/<process_id>/links/<state_str>', methods = ['GET','POST'])
@login_required
def edit_process_links(process_id, state_str):
    #handle state variable for dynamic persistence
    if state_str == 'init':
        state = {}
        state['process'] = as_dict(Process.query.filter_by(id=process_id).first())
        state['inputs'] = query_active_process_links(process_id, 'input_to')
        state['outputs'] = query_active_process_links(process_id, 'output_of')
    else:
        state = eval(urllib.parse.unquote(state_str))

    state_str = urllib.parse.quote(str(state))
    dynamic_input_form = IterativeAddProductForm()
    dynamic_output_form = IterativeAddProductForm()
    dynamic_input_form.submit.label.text = 'Add Input'
    dynamic_output_form.submit.label.text = 'Add Output'
    if request.method == 'POST':
        # remove_input form
        if request.form['form_name'] == 'remove_input':
            delete_inputs = request.form.getlist('removeinput')
            remove_indices = [int(i)-1 for i in delete_inputs]
            state['inputs'] = [i for j, i in enumerate(state['inputs']) if j not in remove_indices]
        # remove_input form
        if request.form['form_name'] == 'add_input':
            if dynamic_input_form.validate_on_submit():
                product = Product.query.filter_by(product_id = dynamic_input_form.product_id.data).first_or_404()
                if not (product.product_id in [i['product_id'] for i in state['inputs']]):
                    state['inputs'].append(as_dict(product))

        #remove_output form
        if request.form['form_name'] == 'remove_output':
            delete_outputs = request.form.getlist('removeoutput')
            remove_indices = [int(i) - 1 for i in delete_outputs]
            state['outputs'] = [i for j, i in enumerate(state['outputs']) if j not in remove_indices]
        #add_output form
        if request.form['form_name'] == 'add_output':
            if dynamic_output_form.validate_on_submit():
                product = Product.query.filter_by(product_id=dynamic_output_form.product_id.data).first_or_404()
                if not (product.product_id in [i['product_id'] for i in state['outputs']]):
                    state['outputs'].append(as_dict(product))

        #return to info
        if request.form['form_name'] == 'return_to_info':
            # alter state_str for former conditinonals
            state_str = urllib.parse.quote(str(state))
            return redirect(url_for('edit_process_info', process_id=process_id, state_str = state_str))
        #submit_changes
        if request.form['form_name'] == 'submit_changes':
            query_message = Inputer.edit_process_links(process_id,state['inputs'],state['outputs'])
            if query_message != 'Success':
                flash(query_message)
                return redirect(url_for('edit_process_links', process_id = process_id,state_str= state_str))

            flash('Links updated')
            # alter state_str for former conditinonals
            state_str = urllib.parse.quote(str(state))
            return redirect(url_for('edit_process_info', process_id = process_id))

        # alter state_str for former conditinonals
        state_str = urllib.parse.quote(str(state))
        #modify session
        return redirect(url_for('edit_process_links', process_id = process_id, state_str = state_str))

    process_name = state['process']['name']
    return render_template('edit_process_links.html',inputs=state['inputs'],outputs = state['outputs'],
                           input_form=dynamic_input_form, output_form = dynamic_output_form,process_name = process_name)

@app.route('/user/all_products', methods = ['GET','POST'])
@login_required
def all_products():
    products = query_all_active_products()
    return render_template('all_products.html', products = products)

@app.route('/user/search_products', methods = ['GET','POST'])
@login_required
def search_products():
    products = query_all_active_products()
    return render_template('all_products.html', products = products)

@app.route('/user/all_processes', methods = ['GET','POST'])
@login_required
def all_processes():
    processes = query_all_active_processes()
    return render_template('all_processes.html', processes = processes)

@app.route('/user/search_processes', methods = ['GET','POST'])
@login_required
def search_processes():
    products = query_all_active_processes()
    return render_template('all_processes.html', products = products)


@app.route('/user/create_product', methods = ['GET','POST'])
@login_required
def create_product():
    form = CreateProductForm()
    if form.validate_on_submit():
        product_id = Inputer.new_product(
            current_user.id,
            name=form.name.data,
            description=form.description.data,
        )

        flash(f'Product "{form.name.data}" created with ID {product_id}')
        return redirect(url_for('create_product'))
    return render_template('create_product.html', form = form)

@app.route('/user/delete_product/<product_id>', methods = ['GET','POST'])
@login_required
def delete_product(product_id):
    product = Product.query.filter_by(owner = session['_user_id'],product_id = product_id, deletion_data = None).first()
    if not product:
        flash(f"User '{session['_user_id']}' does not own product '{product_id}'")
        return redirect(url_for('my_products'))
    else:
        now = datetime.utcnow()
        query_deprecate_product(product_id, now)
        flash(f'Product "{product_id}" deleted')
        return redirect(url_for('my_products'))
