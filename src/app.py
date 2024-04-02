import logging
from flask import Flask, request
from models.plate_reader import PlateReader, InvalidImage
import logging
import io
import requests


def process_number_recognition(ids):
    result = []
    for image_id in ids:
        if int(image_id) not in [10022, 9965]:
            return [image_id], 'invalid image id', 400
        try:
            response = requests.get(f'http://178.154.220.122:7777/images/{image_id}', timeout=5)
        except requests.exceptions.RequestException as e:
            return [image_id], 'Bad Gateway', 502
        im = io.BytesIO(response.content)
        try:
            res = plate_reader.read_text(im)
            result.append(res)
        except InvalidImage:
            logging.error('invalid image')
            return [image_id], 'invalid image', 400
    return result, '', 200


app = Flask(__name__)
plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')


@app.route('/')
def hello():
    user = request.args['user']
    return f'<h1 style="color:red;"><center>Hello {user}!</center></h1>'


# <url>:8080/greeting?user=me
# <url>:8080 : body: {"user": "me"}
# -> {"result": "Hello me"}
@app.route('/greeting', methods=['POST'])
def greeting():
    if 'user' not in request.json:
        return {'error': 'field "user" not found'}, 400

    user = request.json['user']
    return {
        'result': f'Hello {user}',
    }


# <url>:8080/readPlateNumber : body <image bytes>
# {"plate_number": "c180mv ..."}
@app.route('/readPlateNumber/<int:id>', methods=['POST'])
def read_plate_number(id):
    # image_id = request.json['plate_number']
    res, err, code = process_number_recognition([id])
    if err:
        return {
            "error": err
        }, code
    return {
        'plate_number': res
    }, code


@app.route('/readPlateNumbers', methods=['POST'])
def read_plate_numbers():
    image_ids = request.json['plate_numbers']
    res, err, code = process_number_recognition(image_ids)
    if err:
        return {
            "error": err,
            "context": {
                "image_id": res[0]
            }
        }, code
    return {
        'plate_numbers': res
    }, code


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)
