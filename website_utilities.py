from random import choice, randint
import string
import os


def get_chunk(byte1=None, byte2=None, video_path=""):
    full_path = "videos/" + video_path
    file_size = os.stat(full_path).st_size
    start = 0

    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start

    with open(full_path, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk, start, length, file_size


def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    return ''.join(choice(chars) for _ in range(size))


def onetime_generator():
    vowels = ["a", "e", "i", "o", "u"]
    other = [item for item in string.ascii_lowercase if item not in vowels]
    output = ""

    for c in range(2):
        for i in range(randint(5, 7)):
            if i % 2 == 1:
                output += choice(other)
            else:
                output += choice(vowels)
        if c == 0:
            output += "_"

    return output


def reset_short_interactions():
    from app import Video, db

    for i in Video.query.all():
        i.short_term_interaction = 0
        db.session.commit()
