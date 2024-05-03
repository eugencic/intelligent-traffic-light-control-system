from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

from core.rules import *
from core.statistics import *
from core.utils import *

app = Flask(__name__)
CORS(app)


@app.route("/add_traffic_record", methods=["POST"])
def add_traffic_record():
    try:
        data_list = request.get_json()
        if not isinstance(data_list, list) or len(data_list) == 0:
            return jsonify({"error": "Invalid data format. Expected a non-empty list of traffic data."}), 400

        data = data_list[0]

        required_keys = ['time', 'vehicle_count', 'pedestrian_count', 'traffic_light_id']
        if not all(key in data for key in required_keys):
            print(f"Missing keys in data: {set(required_keys) - set(data.keys())}")
            return jsonify({"error": "Invalid data format. Missing required keys."}), 400
        process_real_time_data(data)
        return jsonify({"message": "Traffic data processed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_traffic_rules/<int:intersection_id>", methods=["GET"])
@cross_origin()
def get_traffic_rules(intersection_id):
    try:
        traffic_stats = traffic_intersection_data.get(intersection_id)
        if not traffic_stats:
            return jsonify({"error": "Intersection not found"}), 404

        if intersection_id not in traffic_light_rules:
            return jsonify({"error": "Traffic light durations not available yet"}), 404

        light_durations = traffic_light_rules[intersection_id]
        return jsonify(light_durations), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_background_threads():
    stats_update_thread = threading.Thread(target=update_statistics)
    stats_update_thread.daemon = True
    stats_update_thread.start()

    for intersection_id in traffic_intersection_data:
        update_thread = threading.Thread(target=update_traffic_light_rules, args=(intersection_id,))
        update_thread.daemon = True
        update_thread.start()


if __name__ == '__main__':
    start_background_threads()
    print("Server is listening on port 7000...")
    app.run(host="0.0.0.0", port=7000, debug=False)
