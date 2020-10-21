import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import random
import time

# db = InfluxDBClient('localhost', 8086, 'root', 'root', 'client1_db')
db = InfluxDBClient('192.168.1.10', 8086, 'root', 'root', 'client1_db')
db.create_database('client1_db')


def generate_data():
    measurement_name = "weldingEvents"
    client_name = "client1"
    number_of_points = 250000
    data = []
    for i in range(number_of_points):
        welding_value = format(round(random.uniform(0, 30), 4))
        curr_time = int(time.time() * 1000)
        # curr_time = int(time.time() * 1000000000)
        uniqueID = 'uniqueID' + str(i + 1)
        # data.append("{measurement},client={client},uniqueID={uniqueID} welding_value={welding_value} {timestamp}"
        #            .format(measurement=measurement_name,
        #                    client=client_name,
        #                    uniqueID=uniqueID,
        #                    welding_value=welding_value,
        #                    timestamp=curr_time))
        data.append("{measurement},client={client} welding_value={welding_value} {timestamp}"
                    .format(measurement=measurement_name,
                            client=client_name,
                            welding_value=welding_value,
                            timestamp=curr_time))
    db.write_points(data, database='client1_db', time_precision='n', batch_size=10000,
                    protocol="line")  # previous time_precision='n'


def checkListDuplicates(listOfElems):
    # Check if given list contains any duplicates
    setOfElems = set()
    for elem in listOfElems:
        if elem in setOfElems:
            return True
        else:
            setOfElems.add(elem)
    return False


def get_db_data():
    data = db.query("SELECT * FROM weldingEvents;")
    # print('Data raw: ', data.raw)
    points = data.get_points(tags={'client': 'client1'})
    timestamp_list = []
    for point in points:
        # print("Time: {}, Welding value: {}".format(point['time'], point['welding_value']))
        timestamp_list.append(point['time'])

    if checkListDuplicates(timestamp_list):
        print('Yes, list contains duplicates.\n')
    else:
        print('No duplicates found in list.\n')

    send_data = db.query("SELECT * INTO master_db..weldingEvents FROM client1_db..weldingEvents GROUP BY *;")
    print("Query Successful: ", send_data)
    client.publish("topic/client1", "ALL_INFORMATION_SENT")


def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print("Client1 - error connecting, rc: ", rc)
    else:
        print("Client1 - successfully connected.")
        client.subscribe("topic/master")
        client.subscribe("topic/client2")


def on_message(client, userdata, message):
    decoded_message = str(message.payload.decode("utf-8"))
    print("message received: ", decoded_message)
    print("message topic: ", message.topic)
    print("message qos: ", message.qos)  # 0, 1 or 2.
    print("message retain flag: ", message.retain, "\n")

    if decoded_message == "GET_INFORMATION":
        client.publish("topic/client1", "Starting to send all data related to Client 1.")
        get_db_data()


broker_address = "broker.hivemq.com" # use external broker
# broker_address = "localhost"  # local broker

client = mqtt.Client()  # create new
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address, port=1883)  # connect to broker

generate_data()

client.loop_start()

print("Waiting 4 seconds...\n")
time.sleep(10)

dbs = db.get_list_database()
print('List of DBs: ', dbs)

#################################################

time.sleep(10)  # wait
db.drop_database('client1_db')
client.loop_stop()  # stop the loop
client.disconnect()
