from enums import MoveSlideDirection


class LessonPath:
    def __init__(self, path: str):
        if path is None or path == 'None' or len(path) == 0:
            self.path = []
        else:
            self.path = list(map(int, path.split('.')))

    def add_slide(self, index: int, slide_id: int):
        if slide_id in self.path:
            raise AssertionError(f'Slide {slide_id} already exists in path')
        self.path.insert(index, slide_id)

    def edit_slide(self, index: int, new_slide_id: int):
        self.path[index - 1] = new_slide_id

    def move_slide(self, mode: MoveSlideDirection, index: int):
        match mode:
            case MoveSlideDirection.UP:
                if index == 1:
                    return
                self.path[index - 1], self.path[index - 2] = self.path[index - 2], self.path[index - 1]
            case MoveSlideDirection.DOWN:
                if index == len(self.path):
                    return
                self.path[index - 1], self.path[index] = self.path[index], self.path[index - 1]

    def remove_slide(self, index: int):
        del self.path[index - 1]

    def __str__(self):
        return '.'.join(map(str, self.path))

    def __len__(self):
        return len(self.path)
