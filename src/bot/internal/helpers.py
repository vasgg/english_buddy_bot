import os


def get_image_paths():
    image_dir = "src/bot/internal/data/"
    return [
        os.path.join(image_dir, fname)
        for fname in os.listdir(image_dir)
        if fname.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]