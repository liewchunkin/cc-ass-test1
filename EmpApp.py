from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

# Get Employee
@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template('GetEmp.html')

@app.route("/getempoutput", methods=['POST'])
def GetEmpOutput():
    s3 = boto3.resource('s3')
    emp_id = request.form['emp_id']
    emp_name = ""
    emp_loc = ""
    emp_pri_skill = ""
    emp_img = ""
    selectSQL = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(selectSQL, (emp_id))
    result = cursor.fetchall()
    if(len(result)>0):
        for i in result:
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
            emp_fname = i[1]
            emp_lname = i[2]
            emp_loc = i[4]
            emp_pri_skill = i[3]
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location
            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            cursor.close()
            return render_template('GetEmpOutput.html', emp_id_output=emp_id, fname=emp_fname, lname=emp_lname, emp_loc_output=emp_loc, emp_pri_skill_output=emp_pri_skill, emp_img=object_url)
    else:
        cursor.close()
        return("No User Found")
   


# Delete Employee
@app.route("/delemp", methods=['GET','POST'])
def DelEmp():
    return render_template('DelEmp.html')

@app.route("/delempoutput", methods=['POST'])
def DelEmpOutput():
    emp_id = request.form['emp_id']
    selectSQL = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(selectSQL, (emp_id))
    result = cursor.fetchone()
    if(len(result)>0):
        nameUser = result[1]+" "+result[2]

        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')
        try:
            selectSQL = "DELETE FROM employee WHERE emp_id = %s"
            cursor.execute(selectSQL, (emp_id))
            db_conn.commit()
            print("Data deleted from MySQL RDS... deleting image from S3...")
            boto3.client('s3').delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
        except Exception as e:
            return str(e)

        finally:
            cursor.close()

        print("all modification done...")
        return render_template('DelEmpOutput.html', name=nameUser)
    else:
        cursor.close()
        return("No User Found")
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

    
