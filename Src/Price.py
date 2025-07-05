
class Price:
    initial: int
    final: int

    def __init__(self, initial: int, final: int):
        self.initial = initial
        self.final = final

    def to_dict(self):
        return {
            "initial": self.initial,
            "final": self.final,
        }
    
    @classmethod
    def from_dict(cls, data):   
        return cls(
            initial=data["initial"],
            final=data["final"],
        )