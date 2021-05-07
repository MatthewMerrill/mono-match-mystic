import json
import math
import random
import sys
from typing import *

import numpy as np
from PIL import Image, ImageDraw

__OPERATIONS = {}


def operation(fn: Callable):
    if fn.__name__ in __OPERATIONS:
        raise ValueError(f'Operator {fn.__name__} already registered')
    __OPERATIONS[fn.__name__] = fn
    return fn


@operation
def convert_points():
    positions = []
    while True:
        try:
            pos = [int(input()), int(input())]
            positions.append(pos)
        except EOFError:
            break

    with open('positions.json', 'w') as positions_fp:
        json.dump(positions, positions_fp)


# Mean Squared Error
def MSE(img0, img1):
    np0 = np.array(img0)
    np1 = np.array(img1)
    return np.power((np0 - np1), 2).sum()


@operation
def find_match(card_path0, card_path1):
    print(card_path0, card_path1)

    card_imgs = [Image.open(card_path0), Image.open(card_path1)]
    card_imgs[0].putalpha(256)
    card_imgs[1].putalpha(256)

    icons_by_pos = {0: {}, 1: {}}

    with open('positions.json', 'r') as positions_fp:
        positions = json.load(positions_fp)
        # Shuffle positions for testing determinism
        random.shuffle(positions)

    # icon is at most 200x200
    icon_radius = int(math.hypot(100, 100))
    icon_size = (2 * icon_radius, 2 * icon_radius)

    for card_idx in (0, 1):
        for pos in positions:
            # icon is positioned at 400x400 square where pos is upper left
            icon_at_pos: Image.Image
            icon_at_pos = card_imgs[card_idx].crop((pos[0] + 200 - icon_radius,
                                                    pos[1] + 200 - icon_radius,
                                                    pos[0] + 200 + icon_radius,
                                                    pos[1] + 200 + icon_radius))

            # Blur the image around its center to get rid of rotation
            icon_radially_blurred = Image.new('RGBA', icon_size)
            for rot_deg in range(180):
                rotated_icon = icon_at_pos.rotate(rot_deg * 360 / 180)
                rotated_icon.putalpha(256 // 180)
                icon_radially_blurred.alpha_composite(rotated_icon)

            icons_by_pos[card_idx][tuple(pos)] = (icon_at_pos,
                                                  icon_radially_blurred)

    min_mse = math.inf
    best_match = None

    for pos0, icons0 in icons_by_pos[0].items():
        icon0, radial0 = icons0
        for pos1, icons1 in icons_by_pos[1].items():
            icon1, radial1 = icons1
            mse = MSE(radial0, radial1)
            if mse < min_mse:
                min_mse = mse
                best_match = (pos0, pos1)

    def show_result(img: Image.Image, pos: Tuple[int, int]):
        mask = Image.new('RGBA', (img.width, img.height), color='#222222aa')
        draw = ImageDraw.Draw(mask)

        pos_box = (pos[0] + 200 - icon_radius,
                   pos[1] + 200 - icon_radius,
                   pos[0] + 200 + icon_radius,
                   pos[1] + 200 + icon_radius)

        draw.ellipse(pos_box, fill=(0, 0, 0, 0))

        img.paste(mask, mask=mask)
        img.show()

    for card_idx in (0, 1):
        pos = best_match[card_idx]
        show_result(card_imgs[card_idx], pos)


if __name__ == '__main__':
    if len(sys.argv) <= 1 or sys.argv[1] not in __OPERATIONS:
        print('Missing operation:', ', '.join(__OPERATIONS.keys()))
        print()
        print('You probably want the args:')
        print('find_match cards/file_to_compare.png cards/other_file.png')
        sys.exit(1)

    __OPERATIONS[sys.argv[1]](*sys.argv[2:])

