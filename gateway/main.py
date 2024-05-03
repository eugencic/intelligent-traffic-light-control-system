from flask import Flask, request, jsonify
import requests
import threading

app = Flask(__name__)


def send_request(url, payload, responses, errors, index):
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        responses[index] = response.json()
    except requests.exceptions.RequestException as e:
        errors[index] = str(e)


@app.route('/gateway/add_traffic_record', methods=['POST'])
def gateway():
    data = request.get_json()

    service_a_url = 'http://traffic-analytics-service:8000/add_traffic_record'
    service_b_url = 'http://traffic-regulation-service:7000/add_traffic_record'

    responses = [None, None]
    errors = [None, None]

    threads = []
    for i, url in enumerate([service_a_url, service_b_url]):
        thread = threading.Thread(target=send_request, args=(url, data, responses, errors, i))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    for error in errors:
        if error:
            return jsonify({'error': error}), 500

    return jsonify({'responses': responses}), 200


@app.route('/gateway/get_intersection_info', methods=['GET'])
def get_intersection_info():
    service_url = 'http://localhost:6000/get_intersection_info'

    try:
        response = requests.get(service_url)
        response.raise_for_status()

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
