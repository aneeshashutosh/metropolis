from flask import Flask, redirect, request, jsonify, send_from_directory
from PIL import Image
from io import BytesIO
import base64
from metropolis.metropolis import CubeProblem, PrismProblem
from metropolis.pso import PSO
from metropolis.mh import MH
from metropolis.preprocess import clean
import argparse
app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--port', default='80')
args = parser.parse_args()


@app.route('/')
def home():
    return send_from_directory('', 'index.html')


@app.route('/infer', methods=['GET', 'POST'])
def infer():
    if request.method == 'GET':
        return 'Post an image to this URL!'
    else:
        num_boxes = int(request.form['num_boxes'])
        base64_img = request.form['img']
        img = Image.open(BytesIO(base64.b64decode(base64_img)))
        img = img.convert('RGB')
        if 3 * img.width != 4 * img.height:
            img = img.crop(
                (0, 0, (4/3.) * img.height, img.height)
            )
        img = clean(img)
        img.save('./clean.png')

        all_mins = [0, 0, 0, 2]*num_boxes
        all_maxes = [17, 15, 15, 8]*num_boxes
        problem = CubeProblem(
            None, (400, 300), num_boxes,
            mins=all_mins,
            maxes=all_maxes,
            radius=20
        )
        swarm = PSO(
            zip(all_mins, all_maxes),
            problem.get_likelihood_func
        )
        first_guess = swarm.optimize(
            8, 60, img,
            lambda x: x
        )
        metropolis = MH(
            problem.get_next,
            problem.get_likelihood_func,
            problem.get_prior_prob,
            lambda x: x
        )
        guess = metropolis.optimize(
            img, first_guess, trials=200
        )
        problem.get_image(guess).save('./guess.png')
        obj = [
            {
                "shape": "cube",
                "x": guess[3*i],
                "y": 0,
                "z": guess[3*i+1],
                "l": guess[3*i+2],
                "h": guess[3*i+2],
                "w": guess[3*i+2],
                "xRot": 0,
                "yRot": 0,
                "zRot": 0,
                "r": 1.0,
                "g": 0.0,
                "b": 0.0
            } for i in range(0, num_boxes)
        ]

        return jsonify(obj)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(args.port))
