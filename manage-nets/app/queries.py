from sqlalchemy.sql import text
from app import db
from datetime import datetime
from app.models import Link, Product, Process, User
import pandas as pd


def resultproxy_as_dict(resultproxy):
    return [{column: value for column, value in rowproxy.items()} for rowproxy in resultproxy]

def resultproxy_as_pandas(resultproxy):
    if resultproxy.__class__ == list:
        return pd.DataFrame(resultproxy)
    return pd.DataFrame(resultproxy_as_dict(resultproxy))

def query_user_asset(user_id,asset_type):
    query = f'''
        SELECT * FROM {asset_type}
        WHERE deletion_date IS null AND owner = {user_id}
    '''
    return resultproxy_as_dict(db.session.execute(query))

def query_all_active_products():
    query = '''
    SELECT * FROM product 
    WHERE deletion_date IS null
    '''
    return resultproxy_as_dict(db.session.execute(query))

def query_all_active_processes():
    query = '''
    SELECT * FROM process
    WHERE deletion_date IS null
    '''
    return resultproxy_as_dict(db.session.execute(query))


def query_active_process(process_id):
    query = f'''
        SELECT * FROM Process
        WHERE deletion_date IS null AND process_id = {process_id}
    '''
    return resultproxy_as_dict(db.session.execute(query))

def query_active_product(product_id):
    query = f'''
        SELECT * FROM Product
        WHERE deletion_date IS null AND product_id = {product_id}
    '''
    return resultproxy_as_dict(db.session.execute(query))

def query_active_process_links(process_id, link_type):
    '''get inputs and outputs of process'''
    query1 = f'''
    SELECT product_id FROM link
    WHERE link.process_id = {process_id} AND link.deletion_date is null AND link.link_type = "{link_type}"
    '''
    products = resultproxy_as_dict(db.session.execute(query1))
    prod_tuple = tuple([i['product_id'] for i in products])
    prod_tuple = prod_tuple if len(prod_tuple)>1 else str(prod_tuple).replace(',','')
    query2 = f'''
    SELECT * FROM product
    WHERE product.product_id IN {prod_tuple} and product.deletion_date is null
    '''
    return resultproxy_as_dict(db.session.execute(query2))

def query_active_product_links(product_id, link_type):
    '''get processes linked to product'''
    query1 = f'''
    SELECT process_id FROM link
    WHERE link.product_id = {product_id} AND link.deletion_date is null AND link.link_type = "{link_type}"
    '''
    processes = resultproxy_as_dict(db.session.execute(query1))
    process_tuple = tuple([i['process_id'] for i in processes])
    process_tuple = process_tuple if len(process_tuple)>1 else str(process_tuple).replace(',','')
    query2 = f'''
    SELECT * FROM process
    WHERE process.process_id IN {process_tuple} and process.deletion_date is null
    '''
    return resultproxy_as_dict(db.session.execute(query2))



def query_deprecate_product_links(product_id, now):
    query = f'''
        UPDATE link
        SET deletion_date = datetime("{now}")
        WHERE link.product_id = {product_id} AND link.deletion_date is null
        '''
    return db.session.execute(query)

def query_deprecate_process_links(process_id, now):
    query = f'''
    UPDATE link
    SET deletion_date = datetime("{now}")
    WHERE link.process_id = {process_id} AND link.deletion_date is null
    '''
    return db.session.execute(query)

def query_deprecate_process(process_id, now):
    query = f'''
    UPDATE process
    SET deletion_date = datetime("{now}")
    WHERE process.process_id = {process_id} AND process.deletion_date is null
    '''
    return db.session.execute(query)

def query_deprecate_product(product_id, now):
    query = f'''
        UPDATE product
        SET deletion_date = datetime("{now}")
        WHERE product.product_id = {product_id} AND product.deletion_date is null
        '''
    return db.session.execute(query)

def query_deprecate_product_and_links(product_id, now):
    query_deprecate_product(product_id,now)
    query_deprecate_product_links(product_id,now)
    return

def query_deprecate_process_and_links(process_id,now):
    query_deprecate_process(process_id,now)
    query_deprecate_process_links(process_id,now)
    return

def query_add_links(process_id, products, link_type):
    links = [
        Link(
            process_id=process_id,
            product_id=product_id,
            link_type=link_type
        )
        for product_id in products
    ]
    db.session.add_all(links)
    db.session.commit()
    db.session.close()
    return

def query_add_inputs(process_id,products):
    query_add_links(process_id,products,link_type='input_to')
    return
def query_add_outputs(process_id,products):
    query_add_links(process_id,products,link_type='output_of')
    return

def query_products_output_of(product_ids):
    '''Queries the process that outputs product_id (should be one-to-one)'''
    product_ids = str(tuple(product_ids)) if len(product_ids) > 1 else f'({product_ids[0]})'
    print(product_ids)
    query = f'''
        SELECT process_id, product_id FROM Link
        WHERE product_id in {product_ids} AND deletion_date IS NULL AND link_type = "output_of"  
    '''
    return resultproxy_as_dict(db.engine.execute(query))

def query_add_process_version(process_id, **process_attributes):
    '''adds a process with persisting process_id'''
    process = Process(process_id = process_id, **process_attributes)
    db.session.add(process)
    db.session.commit()
    db.session.close()
    return

def query_add_product_version(product_id, **product_attributes):
    '''adds a product with persisting product_id'''
    product = Process(product_id = product_id, **product_attributes)
    db.session.add(product)
    db.session.commit()
    db.session.close()
    return

class Inputer:
    '''
    module containing methods with business rules for altering database
    all alterations should be made calling one of these methos, avoid calling queries directly
    '''

    @staticmethod
    def new_process(user_id,**user_inputs):
        query = db.engine.execute('''select max(process_id) from Process''')
        max_id = next(query)[0] or 0
        process_id = max_id + 1
        created_by = user_id
        owner = user_id
        process = Process(
            process_id = process_id,
            created_by = created_by,
            owner = owner,
            **user_inputs
        )

        db.session.add(process)
        db.session.commit()
        return process_id

    @staticmethod
    def new_product(user, **user_inputs):
        query = db.engine.execute('''select max(product_id) from Product''')
        max_id = next(query)[0] or 0
        product_id = max_id + 1
        created_by = user
        owner = user
        product = Product(
            product_id=product_id,
            created_by=created_by,
            owner=owner,
            **user_inputs
        )
        db.session.add(product)
        db.session.commit()
        return product_id

    @staticmethod
    def edit_process_links(process_id, new_inputs,new_outputs, **user_inputs):
        #check output links
        if new_outputs:
            former_outputs = resultproxy_as_pandas(query_products_output_of([i['product_id'] for i in new_outputs]))
            if len(former_outputs) > 0:
                has_another_generating_process = former_outputs[former_outputs['process_id'] != process_id]
            else:
                has_another_generating_process = pd.DataFrame(None)
            if has_another_generating_process.any().any():
                return f'products are already outputs of other process:\n{set(has_another_generating_process["product_id"])}'
        #deprecate old
        query_deprecate_process_links(process_id, datetime.utcnow())
        #add new
        if new_inputs:
            query_add_inputs(process_id,[i['product_id'] for i in new_inputs])
            print('add_inputs')
        if new_outputs:
            query_add_outputs(process_id,[i['product_id'] for i in new_outputs])
            print('add_outputs')
        return 'Success'

    @staticmethod
    def edit_process_info(process_id, requester, **new_attributes):
        #todo: check if requester can edit process
        now = datetime.utcnow()
        query_deprecate_process(process_id,now)
        query_add_process_version(process_id, **new_attributes)
        return

    @staticmethod
    def edit_product_info(product_id,requester, **new_attributes):
        now = datetime.utcnow()
        query_deprecate_product(product_id, now)
        query_add_product_version(product_id, **new_attributes)
        return
