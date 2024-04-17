from flask import Flask, jsonify, request

from app.core import *
from app.database.db import *

app = Flask(__name__)
lock = threading.Lock()


@app.route('/add_traffic_record', methods=['POST'])
def add__new_data():
    data = request.json

    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        for record in data:
            cursor.execute(
                "INSERT INTO TrafficRecords (traffic_light_id, time, vehicle_count, pedestrian_count) "
                "VALUES (%s, %s, %s, %s);",
                (record['traffic_light_id'], record['time'], record['vehicle_count'], record['pedestrian_count'])
            )
            conn.commit()

            time_str = record['time']
            traffic_record = {
                "time": time_str,
                "vehicle_count": record['vehicle_count'],
                "pedestrian_count": record['pedestrian_count'],
                "traffic_light_id": record['traffic_light_id']
            }

            with lock:
                traffic_records_cache.append(traffic_record)

        with lock:
            update_frame(data)

        return jsonify({'message': 'Data added successfully'}), 200
    except (Exception,) as e:
        conn.rollback()

        return jsonify({'error': f'Failed to add data: {str(e)}'}), 500
    finally:
        cursor.close()
        return_connection_to_pool(conn)


@app.route('/get_statistics/<int:traffic_light_id>', methods=['GET'])
def get_statistics(traffic_light_id):
    with lock:
        if traffic_light_id in traffic_statistics_cache:
            statistics = traffic_statistics_cache[traffic_light_id]

            return jsonify(statistics)
        else:
            return jsonify({'message': f'Statistics not available for traffic light {traffic_light_id}'}), 404


@app.route('/get_predictions/<int:traffic_light_id>', methods=['GET'])
def predict_vehicle(traffic_light_id):
    hour = request.args.get('hour')
    minute = request.args.get('minute')

    if traffic_light_id is None or hour is None or minute is None:
        return jsonify({'error': 'Missing parameters. Please provide traffic_light_id, hour, and minute.'}), 400
    try:
        traffic_light_id = int(traffic_light_id)
        hour = int(hour)
        minute = int(minute)
    except ValueError:
        return jsonify({'error': 'Invalid parameter types. traffic_light_id, hour, and minute must be integers.'}), 400

    prediction = predict_vehicle_count(hour, minute, traffic_light_id)

    if prediction is None:
        return jsonify({'error': f'No model found for traffic light ID {traffic_light_id}.'}), 404
    return jsonify({'traffic_light_id': traffic_light_id, 'hour': hour, 'minute': minute,
                    'predicted_vehicle_count': prediction}), 200


if __name__ == '__main__':
    setup_database()
    insert_sample_data()
    update_cache()
    init_frame()
    update_statistics()
    df = return_frame()
    train_models_by_intersection(df)
    update_models()
    app.run(host="0.0.0.0", port=8000, debug=False)
