class RFCModelNotInit(Exception):
    def __init__(self):
        super().__init__("You can't calculate break points without model init.")
