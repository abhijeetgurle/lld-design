class ReputationStrategy:
    def __init__(self, increment: int, multiplier: float):
        self._increment = increment
        self._multiplier = multiplier

    @property
    def multiplier(self):
        return self._multiplier

    def on_post(self):
        return self._multiplier * self._increment

    def on_upvote(self):
        return self._increment * self._multiplier

    def on_downvote(self):
        return self._increment * self._multiplier

    def on_delete(self):
        return self._increment * self._multiplier