from flask import Flask, request, jsonify
import mariadb
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure MariaDB connection
config = {
    'host': '127.0.0.1',
    'port': 3305,
    'user': 'root',
    'password': 'root',
    'database': 'govtech_assignment'
}

@app.route("/")
def hello():
  return "Hello World!"

@app.route('/api/applicants', methods=['POST','GET'])
def applicant_action():
    if request.method == 'POST':
        data = request.get_json()
        if ( not data['name'] ):
            return ErrorMessage('Please provide Applicant\'s name')
        
        name = data['name']

        # connection for MariaDB
        conn = mariadb.connect(**config)
        # create a connection cursor
        cur = conn.cursor()

        ## Check if Client exists
        cur.execute("SELECT COUNT(1) FROM ic_clientele WHERE valid_id = (SELECT id FROM ic_valid WHERE name = 'Valid' LIMIT 1) AND name = '" + name + "'")
        rows = cur.fetchall()

        clientExists = False
        for row in rows:
            if ( row[0] > 0 ):
                clientExists = True

        if (not clientExists):
            return ErrorMessage('Applicant does not exist')

        cur.execute("INSERT INTO ic_applicants (clientele_id, valid_id, create_time, change_time) SELECT (SELECT id FROM ic_clientele WHERE valid_id = (SELECT id FROM ic_valid WHERE NAME = 'Valid' LIMIT 1) AND NAME = '" + name + "'), (SELECT id FROM ic_valid WHERE NAME = 'Valid' LIMIT 1), NOW(), NOW()")
        conn.commit()
        cur.close()

        return SuccessMessage("Applicant Added Successfully")

    elif request.method == 'GET':
        # connection for MariaDB
        conn = mariadb.connect(**config)
        # create a connection cursor
        cur = conn.cursor()
        cur.execute("SELECT app.id AS `Application ID`, cli.name AS `Clientele Name`, (SELECT NAME FROM ic_employment_status WHERE id = cli.employment_status_id LIMIT 1) AS `Employment Status`, (SELECT NAME FROM ic_sex WHERE id = cli.sex_id LIMIT 1) AS `Sex`, TO_CHAR(cli.date_of_birth, 'YYYY-MM-DD') AS `Date of Birth`, (SELECT household_id FROM ic_household_clientele WHERE clientele_id = cli.id LIMIT 1) AS `Household ID`, (SELECT clientele_id FROM ic_household_clientele WHERE clientele_id = cli.id LIMIT 1) AS `Clientele ID` FROM ic_applicants app LEFT JOIN ic_clientele cli ON app.clientele_id = cli.id")
        rows = cur.fetchall()
        
        
        application_list = []
        for row in rows:
            application_dict = {}
            application_dict["id"] = row[0]
            application_dict["name"] = row[1]
            application_dict["employment_status"] = row[2]
            application_dict["sex"] = row[3]
            application_dict["date_of_birth"] = row[4]

            household_id = row[5]
            clientele_id = row[6]

            ## Retrieve Household members if available
            cur.execute("SELECT clientele_id AS `Clientele ID`, cli.name AS `Clientele Name`, (SELECT NAME FROM ic_employment_status WHERE id = cli.employment_status_id LIMIT 1) AS `Employment Status`, (SELECT NAME FROM ic_sex WHERE id = cli.sex_id LIMIT 1) AS `Sex`, TO_CHAR(cli.date_of_birth, 'YYYY-MM-DD') AS `Date of Birth`, (SELECT NAME FROM ic_relation WHERE id = hc.relation_id LIMIT 1) AS `Relationship` FROM ic_household_clientele hc LEFT JOIN ic_clientele cli ON hc.clientele_id = cli.id WHERE household_id = '" + household_id + "' AND clientele_id NOT IN ('" + clientele_id + "')")
            rows_household = cur.fetchall()

            household_list = []
            for row in rows_household:
                household_members_dict = {}
                household_members_dict["id"] = row[0]
                household_members_dict["name"] = row[1]
                household_members_dict["employment_status"] = row[2]
                household_members_dict["sex"] = row[3]
                household_members_dict["date_of_birth"] = row[4]
                household_members_dict["relation"] = row[5]
                household_list.append(household_members_dict)
            # application_dict.append({'id': row[0], 'name': row[1], 'email': row[2]})
            application_dict["household"] = household_list
            application_list.append(application_dict)
        
        cur.close()
        return jsonify(application_list)

@app.route('/api/schemes', methods=['GET'])
def schemes_action():
    if request.method == 'GET':
        # connection for MariaDB
        conn = mariadb.connect(**config)
        # create a connection cursor
        cur = conn.cursor()
        cur.execute("SELECT sch.id AS `Scheme ID`, sch.name AS `Scheme Name` FROM ic_schemes sch")
        rows = cur.fetchall()
        
        schemes_list = []
        for row in rows:
            scheme_dict = {}
            scheme_dict["id"] = row[0]
            scheme_dict["name"] = row[1]

            ## Retrieve benefits if available
            cur.execute("SELECT ben.id AS `Benefits ID`, ben.name AS `Name`, FORMAT(ben.amount,2) AS `Amount` FROM ic_schemes_benefits sb LEFT JOIN ic_benefits ben ON sb.benefit_id = ben.id WHERE scheme_id = '" + scheme_dict["id"] + "'")
            rows_schemes_benefits = cur.fetchall()

            benefit_schemes_list = []
            for row in rows_schemes_benefits:
                benefits_dict = {}
                benefits_dict["id"] = row[0]
                benefits_dict["name"] = row[1]
                benefits_dict["amount"] = row[2]
                benefit_schemes_list.append(benefits_dict)
            if benefit_schemes_list: scheme_dict["benefits"] = benefit_schemes_list
            
            ## Retrieve Criterias
            cur.execute("SELECT (SELECT NAME FROM ic_employment_status WHERE id = cri.employment_status_id LIMIT 1) AS `Employment Status`, cri.school_level AS `School Level` FROM ic_criterias cri WHERE scheme_id = '" + scheme_dict["id"] + "' AND cri.valid_id = (SELECT id FROM ic_valid WHERE NAME = 'Valid' LIMIT 1)")
            rows_criteria = cur.fetchall()

            criteria_dict = {}
            for row in rows_criteria:
                if row[0]: criteria_dict["employment_status"] = row[0]
                if row[1]:
                    criteria_dict["has_children"] = {"school_level" : row[1]}
            
            scheme_dict["criteria"] = criteria_dict

            schemes_list.append(scheme_dict)
        
        cur.close()
        return jsonify(schemes_list)
    
@app.route('/api/schemes/eligibility', methods=['GET'])
def schemes_eligibility_action():
    # Retrieve Query Parameters
    applicant_id = request.args.get('applicant')

    if not applicant_id:
        return ErrorMessage('Please provide valid applicant')

    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()

    ## Check if applicant id exists
    cur.execute("SELECT COUNT(1) FROM ic_applicants WHERE id = '" + applicant_id + "'")
    rows_applicant_exists = cur.fetchall()

    applicant_exists = False
    for row in rows_applicant_exists:
        if row[0]: applicant_exists = True

    if not applicant_exists:
        return ErrorMessage('Applicant ID does not exist')

    ## Check the scheme applicant qualifies for
    cur.execute("SELECT (SELECT NAME FROM ic_schemes WHERE id = scheme_id LIMIT 1) AS `Scheme Name` FROM ic_criterias WHERE employment_status_id = (SELECT employment_status_id FROM ic_clientele WHERE id = (SELECT clientele_id FROM ic_applicants WHERE id = '" + applicant_id + "')) AND CASE WHEN sp_calculate_household_primary_age('" + applicant_id + "') > 0 THEN (school_level = 'Primary' OR school_level IS NULL) ELSE school_level IS NULL END")
    rows_scheme_qualified = cur.fetchall()

    applicant_exists = False
    scheme_qualified_list = []
    for row in rows_scheme_qualified:
        scheme_qualified_list.append(row[0])

    if not scheme_qualified_list:
        return ErrorMessage('Applicant is not qualified for any scheme')

    cur.close()
    return jsonify(scheme_qualified_list)

@app.route('/api/applications', methods=['POST','GET'])
def application_action():
    if request.method == 'POST':
        data = request.get_json()
        key_checker = {'applicant_id', 'scheme_id'}

        keys_not_found = key_checker - data.keys()

        if keys_not_found:
            return ErrorMessage('Please provide following parameters: ' + str(keys_not_found))
        
        applicant_id = data['applicant_id']
        scheme_id = data['scheme_id']

        # connection for MariaDB
        conn = mariadb.connect(**config)
        # create a connection cursor
        cur = conn.cursor()

        ## Check if applicant exists
        cur.execute("SELECT COUNT(1) FROM ic_applicants WHERE valid_id = (SELECT id FROM ic_valid WHERE name = 'Valid' LIMIT 1) AND id = '" + applicant_id + "'")
        rows = cur.fetchall()

        applicantExists = False
        for row in rows:
            if ( row[0] > 0 ):
                applicantExists = True

        if (not applicantExists):
            return ErrorMessage('Applicant does not exist')
        
        ## Check if scheme exists
        cur.execute("SELECT COUNT(1) FROM ic_schemes WHERE valid_id = (SELECT id FROM ic_valid WHERE name = 'Valid' LIMIT 1) AND id = '" + scheme_id + "'")
        rows = cur.fetchall()

        schemeExists = False
        for row in rows:
            if ( row[0] > 0 ):
                schemeExists = True

        if (not schemeExists):
            return ErrorMessage('Scheme does not exist')
        
        ## Check if scheme is available for applicant
        cur.execute("SELECT COUNT(1) FROM ic_criterias WHERE employment_status_id = (SELECT employment_status_id FROM ic_clientele WHERE id = (SELECT clientele_id FROM ic_applicants WHERE id = '" + applicant_id + "')) AND CASE WHEN sp_calculate_household_primary_age('" + applicant_id + "') > 0 THEN (school_level = 'Primary' OR school_level IS NULL) ELSE school_level IS NULL END AND scheme_id = '" + scheme_id + "'")
        rows_scheme_qualified = cur.fetchall()

        scheme_qualified = False
        for row in rows_scheme_qualified:
            if row[0]: scheme_qualified = True

        if not scheme_qualified:
            return ErrorMessage('Applicant is not qualified for this scheme')

        ## Check if applicant has valid application already
        cur.execute("SELECT COUNT(1) FROM ic_applications WHERE valid_id = (SELECT id FROM ic_valid WHERE name = 'Valid' LIMIT 1) AND applicant_id = '" + applicant_id + "' AND scheme_id = '" + scheme_id + "'")
        rows_application_exists = cur.fetchall()

        application_exists = False
        for row in rows_application_exists:
            if row[0]: application_exists = True

        if application_exists:
            return ErrorMessage('Application for scheme already exists for applicant')

        ## Add Record into Application Table
        cur.execute("INSERT INTO ic_applications (applicant_id, scheme_id, valid_id, create_time, change_time) SELECT '" + applicant_id + "', '" + scheme_id + "',(SELECT id FROM ic_valid WHERE NAME = 'Valid' LIMIT 1), NOW(), NOW()")
        conn.commit()
        cur.close()

        cur.close()
        
        return SuccessMessage("Applicant Added Successfully")

    elif request.method == 'GET':
        # connection for MariaDB
        conn = mariadb.connect(**config)
        # create a connection cursor
        cur = conn.cursor()
        cur.execute("SELECT id, (SELECT (SELECT NAME FROM ic_clientele WHERE id = app.clientele_id) FROM ic_applicants app WHERE app.id = applicant_id LIMIT 1) AS `Name`, (SELECT NAME FROM ic_schemes WHERE id = scheme_id LIMIT 1) AS `Scheme` FROM ic_applications WHERE valid_id = (SELECT id FROM ic_valid WHERE NAME = 'Valid' LIMIT 1)")
        rows = cur.fetchall()
        
        application_list = []
        for row in rows:
            application_dict = {}
            application_dict["id"] = row[0]
            application_dict["name"] = row[1]
            application_dict["scheme"] = row[2]

            application_list.append(application_dict)
        
        cur.close()
        return jsonify(application_list)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data['name']
    email = data['email']
    
    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    conn.commit()
    cur.close()

    print('name: ' + name, file=sys.stderr)
    print('email: ' + email, file=sys.stderr)
    # print('This is error output', file=sys.stderr)
    # print('This is standard output', file=sys.stdout)
    # print('enter getJSONReuslt', flush=True)
    
    return jsonify({'message': 'User added successfully'}), 201

# @app.route('/users/<int:id>', methods=['PUT'])
# def update_user(id):
#     data = request.get_json()
#     name = data['name']
#     email = data['email']
    
#     cur = mysql.connection.cursor()
#     cur.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (name, email, id))
#     mysql.connection.commit()
#     cur.close()
    
#     return jsonify({'message': 'User updated successfully'})

# @app.route('/users/<int:id>', methods=['DELETE'])
# def delete_user(id):
#     cur = mysql.connection.cursor()
#     cur.execute("DELETE FROM users WHERE id=%s", (id,))
#     mysql.connection.commit()
#     cur.close()
    
#     return jsonify({'message': 'User deleted successfully'})

def ErrorMessage(msg):
    return {'Status':'Failed', 'Message':msg}

def SuccessMessage(msg):
    return {'Status':'Success', 'Message':msg}

if __name__ == '__main__':
    app.run(debug=True)
