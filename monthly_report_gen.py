#!/usr/bin/env python3
'''Python script to run monthly and return a custom report using data from the TutorCruncher API'''
import pprint, requests, json
import datetime
import sys
import yagmail

api_key = ''

headers = {'Authorization': 'token ' + api_key}

# Gets all appointments
r = requests.get('https://secure.tutorcruncher.com/api/appointments/', headers=headers)

# Sort by date - only want previous months (run cronjob at the begining of a new month (day 1-4)) - by finish date
# Sort by status = complete or cancelled but chargeable
# If Charge type = hourly, units = length/hr, One off
response = r.json()
service_list = []
lesson_service_dict = {}
for data in response['results']:
    try:
        date = datetime.datetime.fromisoformat(data['finish'])
    except:
        try:
            date = datetime.datetime.fromisoformat(data['finish'][:-1] + '+00:00')
        except:
            continue

    sub = 1
    if len(sys.argv) > 1:
        current_month = int(sys.argv[1])
        if sys.argv[1] == "mid_month":
            sub = 0
    else:
        current_month = datetime.datetime.now(datetime.timezone.utc).month

    month = int(current_month) - sub
    if month <= 0:
        month = 11
    # Get a list of service ids with completed or chargeable orders in the specified month (previous month if unspecified)
    # Store all service ids in a dictionary as the key with a list of corresponding lessons as values
    if (data['status'] == "complete" or data['status'] == "cancelled-chargeable") and int(date.month) == month:
        # Get rate info then calculate revenue, hours and profit
        try:
            lesson_service_dict[data['service']['id']].append(data['id'])
        except:
            lesson_service_dict[data['service']['id']] = []
            lesson_service_dict[data['service']['id']].append(data['id'])

# Each service id is one row in the outputted table
for key in lesson_service_dict:
    client_managers_list = []
    client_managers = ""
    service_revenue = 0
    service_profit = 0
    client_names = []
    client_ids = []
    clients = ""
    for lesson in lesson_service_dict[key]:
        try:
            r = requests.get('https://secure.tutorcruncher.com/api/appointments/' + str(lesson) + '/', headers=headers)
            response = r.json()
        except:
            print("Error retreiving individual appointment by id.")
            continue
        # Get rate info then calculate revenue, hours and profit, client here or? - get all clients
        # Get total number of hours
        try:
            hours = float(response['units'])
        except:
            print("Error retreiving number of hours.")
            # TODO: add warning in table that says this meeting charge type is not hourly. Please double check, for any continue statement
            continue
        # Calculate - recipient/student/client revenue
        try:
            student_charge_rate = 0
            for student in response['rcras']:
                student_charge_rate += float(student['charge_rate'])
                # Get client name. Default to student name if None.
                try:
                    if student['paying_client_name']:
                        client_names.append(student['paying_client_name'])
                        client_ids.append(student['paying_client'])
                    else:
                        client_names.append(student['recipient_name'])
                except:
                    print("Unable to find client name or student name.")
        except:
            print("Error retreiving recipient/client/student charge rate.")
            continue
        # Calculate - contractor/tutor pay
        try:
            tutor_pay_rate = 0
            for tutor in response['cjas']:
                tutor_pay_rate += float(tutor['pay_rate'])
        except:
            print("Error retreiving tutor/contractor charge rate.")
            continue
        # Caclulate the profit and revenue for the individual service/appointment
        try:
            service_revenue = service_revenue + (hours * student_charge_rate)
            service_profit = service_profit + (hours * tutor_pay_rate)
        except:
            print("Error calculating service's revenue and profit for a lesson/appointment.")
            continue
    clients = ",".join(list(set(client_names)))
    client_ids = list(set(client_ids))
    # Get client managers from the list of clients
    for id in client_ids:
        r = requests.get('https://secure.tutorcruncher.com/api/clients/' + str(id) + '/', headers=headers)
        response = r.json()
        if response['associated_admin'] is not None:
            client_managers_list.append(response['associated_admin']['first_name'] + " " + response['associated_admin']['last_name'])
        else:
            print("No associated client manager")
            client_managers_list.append("No Associated Client Manager")
    client_managers = ",".join(list(set(client_managers_list)))
    print(clients)
    print(service_revenue)
    print(service_profit)
    print(month)
    print(client_managers)

yag = yagmail.SMTP({'verify982@gmail.com': 'TutorHelper'}, '')
# yag = yagmail.SMTP()
contents = ['This is the body, and here is just text http://somedomain/image.png',
            'You can find an audio file attached.']
yag.send('lgigliozzi@ryerson.ca', 'subject', contents)

# Format properly now
# Send email with table
