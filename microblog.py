from app import app, db
from app.models import User, Process, Product, Link

@app.shell_context_processor
def make_shell_context():
    return {'db':db, 'User':User, 'Product':Product, 'Process':Process, 'Link':Link}

if __name__ == '__main__':
    app.run(debug = True)