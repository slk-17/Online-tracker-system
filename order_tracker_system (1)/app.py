from flask import Flask, render_template, url_for, request
import sqlite3
import os
from datetime import datetime
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode
import cv2
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':

        connection = sqlite3.connect('DataBase.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT name, password FROM user WHERE name = '"+name+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchall()

        if len(result) == 0:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')
        else:
            return render_template('box.html', msg='Successfully login')

    return render_template('index.html')


@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':

        connection = sqlite3.connect('DataBase.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']

        command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
        cursor.execute(command)

        query = "SELECT * FROM user WHERE email = '"+email+"'"
        cursor.execute(query)

        result = cursor.fetchall()
        if len(result) == 0:
            cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
            connection.commit()

            return render_template('index.html', msg='Successfully Registered')
        else:
            return render_template('index.html', msg='Email already exists')
    
    return render_template('index.html')


@app.route('/logout')
def logout():
    return render_template('index.html')

@app.route('/box')
def box():
    return render_template('box.html')


@app.route('/boxtrack', methods=['GET', 'POST'])
def boxtrack():
    if request.method == 'GET':

        connection = sqlite3.connect('DataBase.db')
        cursor = connection.cursor()

        boxNum = request.args.get('boxes')
        items = request.args.getlist('items')

        qr = qrcode.QRCode(
                version =1,
                box_size =10,
                border=6)
        qr.add_data(boxNum)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color= "white")
        image.save('static/'+boxNum+'.png')

        itemlist=''
        for i in items:
            itemlist += i+' '

        command = """CREATE TABLE IF NOT EXISTS boxtracking(boxNum TEXT, items TEXT, timeleft TEXT, timereached TEXT, progress)"""
        cursor.execute(command)

        query = "SELECT * FROM boxtracking WHERE boxNum = '"+boxNum+"'"
        cursor.execute(query)

        result = cursor.fetchall()

        if len(result) == 0:

            cursor.execute("INSERT INTO boxtracking (boxNum, items) VALUES ('"+boxNum+"', '"+itemlist+"')")
            connection.commit()

            return render_template('box.html')
        else:
            return render_template('box.html', msg='Van number already exists')

    return render_template('box.html')

@app.route('/scanbox')
def scanbox():
    
    connection = sqlite3.connect('DataBase.db')
    cursor = connection.cursor()
    
    vs = cv2.VideoCapture(0)
    while True:
        ret, img = vs.read()
        detectedBarcodes = decode(img)
        d=''
        t=''
        for barcode in detectedBarcodes:
            d = barcode.data
            t = barcode.type
        if d != "":
            break
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.release()
    cv2.destroyAllWindows()
    d = d.decode("utf-8")
    print(d)

    query = "SELECT * FROM boxtracking WHERE boxNum = '"+d+"'"
    cursor.execute(query)

    result = cursor.fetchall()

    row = result[0]
    (boxnum, items, timeleft, timereach, progress) = row

    if progress is None:
        progress = 0

    names=['Box Number', 'Items', 'Time Left', 'Time Reached', 'Progress']
    Result=[]

    if int(progress) != 100:
        if int(progress) == 0:
            today = str(datetime.now())
            prog = '25'
            query="UPDATE boxtracking set progress = '"+prog+"', timeleft ='"+today+"'  where boxNum = '"+boxnum+"'"
            cursor.execute(query)
            connection.commit()

            Result.append(boxnum)
            Result.append(items)
            Result.append(today)
            Result.append(timereach)
            Result.append(prog)
            return render_template('box.html', result=result, names=names, title='Box Tracking')
        else:
            if int(progress) == 75:
                today = str(datetime.now())
                timereach = today
                query="UPDATE boxtracking set timereached = '"+timereach+"' where boxNum = '"+boxnum+"'"
                cursor.execute(query)
                connection.commit()
            prog = str(int(progress)+25)
            query="UPDATE boxtracking set progress = '"+prog+"' where boxNum = '"+boxnum+"'"
            cursor.execute(query)
            connection.commit()

            Result.append(boxnum)
            Result.append(items)
            Result.append(timeleft)
            Result.append(timereach)
            Result.append(prog)
            return render_template('box.html', result=result, names=names, title='Box Tracking')
    else:

        Result.append(boxnum)
        Result.append(items)
        Result.append(timeleft)
        Result.append(timereach)
        Result.append(progress)
        return render_template('box.html', result=result, names=names, title='Box Tracking')

@app.route('/boxData')
def boxData():
    connection = sqlite3.connect('DataBase.db')
    cursor = connection.cursor()

    query = "SELECT * FROM boxtracking"
    cursor.execute(query)

    result = cursor.fetchall()
    if len(result) == 0:
        return render_template('box.html', msg='Data not found')
    else:
        names=['Box Number', 'Items', 'Time Left', 'Time Reached', 'Progress']

        return render_template('box.html', result=result, names=names, title='Box Tracking')

@app.route('/Removebox/<Number>')
def Removebox(Number):
    connection = sqlite3.connect('DataBase.db')
    cursor = connection.cursor()

    cursor.execute("DELETE FROM boxtracking WHERE boxNum = '"+Number+"'")
    connection.commit()

    return render_template('box.html', msg='Data successfully deleted with van number: {}'.format(Number))

if __name__ == "__main__":
    app.run(debug=True)
