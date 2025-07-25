# rnu.py


from kouteihyo_app import app
print("SECRET_KEY:", app.config['SECRET_KEY'])


if __name__ == '__main__':
    app.run(debug=True, port=5010)
