from time import sleep_us
from machine import Pin, PWM, Timer
from sys import platform

from utils import Note

silence = 48000
inf = 1 << 30


# Function to calculate the frequency of a musical note based on its MIDI note number
def get_freq(note):
    return int(440 * 2 ** ((note - 69) / 12.0))


# generic PWM
class GPWM:
    def __init__(self, pin, vol=None, freq=440, duty_u16=0) -> None:
        if platform == "rp2":
            self.pwm = PWM(pin)
            self.pwm.freq(freq)
            self.pwm.duty_u16(duty_u16)
        else:
            self.pwm = PWM(pin, freq=freq, duty_u16=duty_u16)

        if vol:
            self.vol = vol
            self.vol.on()

    def freq(self, freq=None):
        if freq:
            self.pwm.freq(freq)
        else:
            return self.pwm.freq()

    def duty_u16(self, duty_u16=None):
        if duty_u16:
            self.pwm.duty_u16(duty_u16)
        else:
            return self.pwm.duty_u16()


class SoundManager:
    def __init__(self, pins) -> None:
        self.keyframe = inf
        self.pwms = []
        for pin in pins:
            self.pwms.append(
                GPWM(Pin(pin), vol=Pin(pin - 1, Pin.OUT), freq=silence, duty_u16=32768)
            )
        self.avi = [i for i in range(len(self.pwms))]  # 可用pin
        self.stop = [inf for _ in range(len(self.pwms))]  # 当前音的停止时间
        self.track = [-1 for _ in range(len(self.pwms))]

    def init(self):
        for pwm in self.pwms:
            pwm.freq(silence)

    def update(self, time):
        for i in range(len(self.pwms)):
            if time >= self.stop[i]:
                self.pwms[i].freq(silence)
                self.avi.append(i)
                self.stop[i] = inf
        return min(self.stop)

    def add(self, note):  # start aka time
        # TODO: inst
        idx = -1
        if len(self.avi) == 0:  # try to stop some same track note
            tracks = set()
            for i in range(len(self.pwms)):
                if self.track[i] in tracks:
                    idx = i
                    break
                else:
                    tracks.add(self.track[i])
            if idx == -1:
                print("no aviliable pin")
                return
        else:
            idx = self.avi.pop()

        self.pwms[idx].freq(get_freq(note.noteid))
        self.stop[idx] = note.start + note.duration
        self.track[idx] = note.track

    def silence(self):
        for i in range(len(self.pwms)):
            self.pwms[i].freq(silence)
        self.avi = [i for i in range(len(self.pwms))]


class SBConfig:
    def __init__(self, tracks) -> None:
        self.map = {track: None for track in tracks}
        self.snds = set()

    def init(self):
        for snd in self.snds:
            snd.init()

    def update(self, time):
        return min([snd.update(time) for snd in self.snds])

    def set_snd(self, tracks, snd):
        for track in tracks:
            self.map[track] = snd
        self.snds.add(snd)

    def silence(self):
        for snd in self.snds:
            snd.silence()

    def add(self, note: Note):
        playsnd = self.map[note.track]
        playsnd.add(note)


class SB:
    def __init__(self, filename, sbconfig: SBConfig = None) -> None:
        self.tempo = 500000
        self.notes = []
        self.conf = sbconfig

        self.time = 0
        with open(filename) as f:
            line = "START"
            while line != "":
                line = f.readline()
                args = line.split(" ")
                if args[0] == "tempo":
                    tempo = int(args[1])
                    self.tempo = tempo
                    print("tempo: {}".format(tempo))
                elif args[0] == "note":
                    self.notes.append(Note.load(args))

    def init(self):
        self.time = 0
        self.cur_note = 0
        self.conf.init()

    def update(self, time):
        while (
            self.cur_note < len(self.notes) and self.notes[self.cur_note].start == time
        ):
            self.conf.add(self.notes[self.cur_note])
            self.cur_note += 1

        next_time = self.conf.update(time)

        return min(
            next_time,
            self.notes[self.cur_note].start if self.cur_note < len(self.notes) else inf,
        )

    def play(self):
        self.init()

        next_time = self.update(self.time)
        while next_time < inf:
            self.goto(next_time)
            next_time = self.update(self.time)

        self.silence()

    def silence(self):
        self.conf.silence()

    def goto(self, time):
        tosleep = (time - self.time) * self.tempo / 480
        sleep_us(int(tosleep))
        self.time = time
