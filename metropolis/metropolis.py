import random
import numpy as np
from Tkinter import Label
from utils import draw_from_model
from PIL import Image, ImageDraw, ImageFilter, ImageTk


class SquareProblem(object):
    def __init__(self, root, dims, side, color, radius):
        self.root = root
        self.dims = dims
        self.side = side
        self.color = color
        self.radius = radius

    def render(self, img):
        blurred = img.filter(
            ImageFilter.GaussianBlur(radius=self.radius)
        )

        tk_img = ImageTk.PhotoImage(blurred)
        label_image = Label(self.root, image=tk_img)
        label_image.place(
            x=0, y=0,
            width=img.size[0],
            height=img.size[1]
        )
        self.root.update()

    def get_image(self, polygon):
        data = np.zeros(
            (self.dims[1], self.dims[0], 3),
            dtype=np.uint8
        )
        data.fill(255)
        img = Image.fromarray(data, 'RGB')
        draw = ImageDraw.Draw(img, 'RGB')
        draw.polygon(polygon['points'], polygon['color'])
        del draw
        return img

    def get_random_square(self):
        center = (
            random.randrange(
                self.side/2., self.dims[0] - self.side/2.
            ),
            random.randrange(
                self.side/2., self.dims[1] - self.side/2.
            )
        )
        return self.get_square(center, self.side, self.color)

    # center is (x, y), side is side length in px
    def get_square(self, center, side, color):
        top_left = tuple(np.add(center, (-side/2., -side/2.)))
        top_right = tuple(np.add(center, (side/2., -side/2.)))
        bot_right = tuple(np.add(center, (side/2., side/2.)))
        bot_left = tuple(np.add(center, (-side/2., side/2.)))
        return {
            'points': [
                top_left,
                top_right,
                bot_right,
                bot_left
            ],
            'color': color
        }

    # G
    def get_next(self, x):
        step = 80
        shift = (
            random.randrange(-step, step),
            random.randrange(-step, step)
        )

        x_left_shift = x['points'][0][0] + shift[0]
        x_right_shift = x['points'][2][0] + shift[0]
        y_top_shift = x['points'][0][1] + shift[1]
        y_bot_shift = x['points'][2][1] + shift[1]

        if x_left_shift < 0 or x_right_shift > self.dims[0]:
            shift = (0, shift[1])
        if y_top_shift < 0 or y_bot_shift > self.dims[1]:
            shift = (shift[0], 0)

        return {
            'points': [
                tuple(np.add(x['points'][0], shift)),
                tuple(np.add(x['points'][1], shift)),
                tuple(np.add(x['points'][2], shift)),
                tuple(np.add(x['points'][3], shift)),
            ],
            'color': x['color']
        }

    def get_likelihood_func(self, answer):
        answer_img = self.get_image(answer)
        blurred_a = answer_img.filter(
            ImageFilter.GaussianBlur(radius=self.radius)
        )
        blurred_data_a = np.array(blurred_a.getdata())[:, 0]
        data_a = np.array(answer_img.getdata())[:, 0]

        def get_likelihood(x):
            b = self.get_image(x)
            blurred_b = b.filter(
                ImageFilter.GaussianBlur(radius=self.radius)
            )
            blurred_data_b = np.array(blurred_b.getdata())[:, 0]
            data_b = np.array(b.getdata())[:, 0]

            blurred_diff = np.subtract(blurred_data_a, blurred_data_b)
            diff = np.subtract(data_a, data_b)
            return 1./(np.linalg.norm(blurred_diff) + np.linalg.norm(diff))

        return get_likelihood

    def get_prior_prob(self, x):
        return 1.


class CubeProblem(object):
    def __init__(self, root, dims, num_boxes, mins, maxes, radius):
        self.root = root
        self.dims = dims
        self.num_boxes = num_boxes
        self.mins = mins
        self.maxes = maxes
        self.radius = radius

    def render(self, img, x):
        img = self.get_image(x).filter(
            ImageFilter.GaussianBlur(radius=self.radius)
        )
        draw = ImageDraw.Draw(img)
        draw.text((30, 10), str([round(c, 3) for c in x]), fill="#000000")
        tk_img = ImageTk.PhotoImage(img)
        label_image = Label(self.root, image=tk_img)
        label_image.place(
            x=0, y=0,
            width=img.size[0],
            height=img.size[1]
        )
        self.root.update()

    def get_image(self, x):
        model = [
            [20, (0, 0, 0), '#000000', 1]
        ] + [[
            x[4*i+3],
            (x[4*i], x[4*i+1], x[4*i+2]),
            '#ff0000',
            0
        ] for i in range(0, self.num_boxes)] + [
            [20, (20.1, 0, 0), '#ffffff', 0]
        ]
        return self.get_image_helper(model)

    def get_image_helper(self, model):
        im = Image.new('RGB', self.dims, '#ffffff')
        draw = ImageDraw.Draw(im)
        camera = np.matrix([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [15, 10, 30]
        ])
        draw_from_model(draw, camera, model, fov=200)
        return im

    def get_random_cube(self):
        return [
            random.uniform(self.mins[i], self.maxes[i])
            for i in range(0, len(self.mins))
        ]

    # G
    def get_next(self, x, k, factor):
        step = (self.maxes[k]-self.mins[k])/8.
        shift = factor * random.uniform(0, step)

        if x[k] + shift < self.mins[k] or x[k] + shift > self.maxes[k]:
            return x
        else:
            x_list = list(x)
            x_list[k] += shift
            return tuple(x_list)

    def get_likelihood_func(self, goal_img):
        small_size = (100, 75)
        small_goal_img = goal_img.resize(
            small_size, Image.BILINEAR
        ).filter(
            ImageFilter.GaussianBlur(radius=self.radius)
        )
        data_a = np.array(small_goal_img.getdata())

        def get_likelihood(x):
            b = self.get_image(x).resize(
                small_size, Image.BILINEAR
            ).filter(
                ImageFilter.GaussianBlur(radius=self.radius)
            )
            data_b = np.array(b.getdata())

            # direct error
            a_sub_b = np.subtract(data_a, data_b)
            diff = np.linalg.norm(
                a_sub_b[:, 0]
            ) + np.linalg.norm(
                a_sub_b[:, 1]
            ) + np.linalg.norm(
                a_sub_b[:, 2]
            )
            return 1./diff

        return get_likelihood

    def get_prior_prob(self, x):
        return 1.


class PrismProblem(CubeProblem):
    def get_image(self, x):
        model = [
            [20, (0, 0, 0), '#000000', 1]
        ] + [[
            (x[5*i+2], x[5*i+3], x[5*i+4]),
            (x[5*i], 0, x[5*i+1]),
            '#ff0000',
            0
        ] for i in range(0, self.num_boxes)] + [
            [20, (20.1, 0, 0), '#ffffff', 0]
        ]
        return self.get_image_helper(model)


class FurnitureProblem(CubeProblem):
    def get_furniture_from_type(self, y, x):
        t = int(y)
        if t == 1:
            return [
                (x[0], x[1], x[2]),
                (0, 0, x[3]),
                '#ff0000',
                0
            ]
        elif t == 2:
            return [
                (x[0], x[1], x[2]),
                (x[3], 0, 0),
                '#ff0000',
                0
            ]
        elif t == 3:
            return [
                (x[0], x[1], x[2]),
                (20-x[0], 0, x[3]),
                '#ff0000',
                0
            ]
        else:
            return [
                (0, 0, 0),
                (0, 0, 0),
                '#ff0000',
                0
            ]

    def get_next(self, x, k, factor):
        if k % 5 == 0:
            new_type = random.randrange(0, 4)
            x_list = list(x)
            x_list[k] = new_type
            return tuple(x_list)
        else:
            step = (self.maxes[k]-self.mins[k])/8.
            shift = factor * random.uniform(0, step)

            if x[k] + shift < self.mins[k] or x[k] + shift > self.maxes[k]:
                return x
            else:
                x_list = list(x)
                x_list[k] += shift
                return tuple(x_list)

    def get_image(self, x):
        model = [
            [(20, 20, 20), (0, 0, 0), '#000000', 1]
        ] + [self.get_furniture_from_type(
            x[i*5], x[i*5+1:(i+1)*5]
        ) for i in range(0, self.num_boxes)]
        return self.get_image_helper(model)

    def get_likelihood_func(self, goal_img):
        small_size = (100, 75)
        small_goal_img = goal_img.resize(
            small_size, Image.BILINEAR
        ).filter(
            ImageFilter.GaussianBlur(radius=self.radius)
        )
        data_a = np.array(small_goal_img.getdata())

        def get_likelihood(x):
            b = self.get_image(x).resize(
                small_size, Image.BILINEAR
            ).filter(
                ImageFilter.GaussianBlur(radius=self.radius)
            )
            data_b = np.array(b.getdata())

            # direct error
            a_sub_b = np.subtract(data_a, data_b)
            diff = np.linalg.norm(
                a_sub_b[:, 0]
            ) + np.linalg.norm(
                a_sub_b[:, 1]
            ) + np.linalg.norm(
                a_sub_b[:, 2]
            )
            return 1./diff

        return get_likelihood
