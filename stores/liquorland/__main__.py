from stores import liquorland, generic_store


class Liquorland(generic_store):

    def __init__(self):
        self.model = liquorland.model.LiquorlandModel()
