from time import sleep_us
from machine import Pin, PWM, Timer
from sys import platform
import config

from utils import Note

silence = 48000
inf = 1 << 30


# Function to calculate the frequency of a musical note based on its MIDI note number
def get_freq(note):
    return int(440 * 2 ** ((note - 69) / 12.0))


# maybe we need a more accurate function
def get_duty(vol):
    return int(vol * 65535)


class Buzzer:
    KEEP = 0
    SOFT = 1

    def __init__(self, mode, pin, vol=None, freq=silence, duty_u16=32768) -> None:
        self.mode = mode
        self.max_vol = 1
        self.keyframe = []

        if platform == "rp2":
            self.pwm = PWM(Pin(pin))
            self.pwm.freq(freq)
            self.pwm.duty_u16(duty_u16)
        else:
            self.pwm = PWM(Pin(pin), freq=freq, duty_u16=duty_u16)

        # if Buzzer is in SOFT mode, there must be a volumn pin
        if mode == Buzzer.KEEP:
            if vol:
                self.vol = Pin(vol, Pin.OUT)
            else:
                self.vol = None
        elif mode == Buzzer.SOFT:
            self.vol = PWM(Pin(vol))
            self.vol.freq(config.vol_freq)
        self.set_vol(1)

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

    def silence(self):
        self.keyframe = []
        self.pwm.freq(silence)

    def set_max_vol(self, max_vol):
        self.max_vol = max_vol

    def set_vol(self, vol):
        if self.vol == None:
            return
        if self.mode == Buzzer.KEEP:
            if vol:
                self.vol.on()
            else:
                self.vol.off()
        elif self.mode == Buzzer.SOFT:
            vol = min(1, max(0, vol))
            self.vol.duty_u16(get_duty(vol * self.max_vol))

    def update(self, time):
        while len(self.keyframe) and time >= self.keyframe[0][0]:
            _, vol = self.keyframe.pop(0)
            self.set_vol(vol)
        if len(self.keyframe):
            return self.keyframe[0][0]
        else:
            return inf

    def play(self, note):
        self.freq(get_freq(note.noteid))
        self.set_vol(1)
        self.keyframe = []
        if self.mode == Buzzer.SOFT:
            for t, vol in config.vol_time:
                self.keyframe.append((note.start + t, vol))

    def test(self):
        self.set_vol(1)
        for i in [60, 62, 64, 65, 67, 69, 71]:
            self.freq(get_freq(i))
            sleep_us(500000)
        self.silence()


class SoundManager:
    def __init__(self, buzzers, max_vol=1) -> None:
        self.keyframe = inf
        self.buzzers = buzzers
        for buzzer in self.buzzers:
            buzzer.set_max_vol(max_vol)
        self.avi = [i for i in range(len(self.buzzers))]  # 可用Buzzer
        self.stop = [inf for _ in range(len(self.buzzers))]  # 当前音的停止时间
        self.track = [-1 for _ in range(len(self.buzzers))]  # 当前音的音轨

    def init(self):
        for buzzer in self.buzzers:
            buzzer.silence()

    def update(self, time):
        for i in range(len(self.buzzers)):
            if time >= self.stop[i]:
                self.buzzers[i].silence()
                self.avi.append(i)
                self.stop[i] = inf
        return min(min(self.stop), min([i.update(time) for i in self.buzzers]))

    def add(self, note):  # start aka time
        # TODO: inst
        idx = -1
        if len(self.avi) == 0:  # try to stop some same track note
            tracks = set()
            for i in range(len(self.buzzers)):
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

        self.buzzers[idx].play(note)
        self.stop[idx] = note.start + note.duration
        self.track[idx] = note.track

    def silence(self):
        for i in range(len(self.buzzers)):
            self.buzzers[i].silence()
        self.avi = [i for i in range(len(self.buzzers))]


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
        print(f"goto {time}")
