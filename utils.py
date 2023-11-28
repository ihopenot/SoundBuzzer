class Note:
    def __init__(self, inst=0, noteid=0, start=0, duration=0, track=0) -> None:
        self.inst = inst
        self.noteid = noteid
        self.start = start
        self.duration = duration
        self.track = track

    def load(blob):
        ret = Note()
        ret.inst = int(blob[1])
        ret.noteid = int(blob[2])
        ret.start = int(blob[3])
        ret.duration = int(blob[4])
        ret.track = int(blob[5])
        return ret

    def save(self):
        return "note {} {} {} {} {}\n".format(
            self.inst, self.noteid, self.start, self.duration, self.track
        )
