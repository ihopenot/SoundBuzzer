from time import sleep
from machine import Pin, PWM
from sys import platform

silence = 48000
inf = 1 << 30


# Function to calculate the frequency of a musical note based on its MIDI note number
def get_freq(note):
    return int(440 * 2 ** ((note - 69) / 12.0))


# generic PWM
class GPWM:
    def __init__(self, pin, freq=440, duty_u16=0) -> None:
        if platform == "rp2":
            self.pwm = PWM(pin)
            self.pwm.freq(freq)
            self.pwm.duty_u16(duty_u16)
        else:
            self.pwm = PWM(pin, freq=freq, duty_u16=duty_u16)

    def freq(self, freq):
        self.pwm.freq(freq)

    def duty_u16(self, duty_u16):
        self.pwm.duty_u16(duty_u16)


class SoundManager:
    def __init__(self, pins) -> None:
        self.keyframe = inf
        self.pwms = []
        for pin in pins:
            self.pwms.append(GPWM(Pin(pin), freq=silence, duty_u16=32768))
        self.avi = [i for i in range(len(self.pwms))]  # 可用pin
        self.stop = [inf for _ in range(len(self.pwms))]  # 当前音的停止时间
        self.track = [-1 for _ in range(len(self.pwms))]

    def need_int(self):
        return self.keyframe

    def update_keyframe(self):
        self.keyframe = min(self.stop)

    def add(self, inst, nodeid, start, duration, track):  # start aka time
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

        self.pwms[idx].freq(get_freq(nodeid))
        self.stop[idx] = start + duration
        self.track[idx] = track
        self.update_keyframe()

    def interval(self, time):
        for i in range(len(self.pwms)):
            if time >= self.stop[i]:
                self.pwms[i].freq(silence)
                self.avi.append(i)
                self.stop[i] = inf
        self.update_keyframe()

    def silence(self):
        for i in range(len(self.pwms)):
            self.pwms[i].freq(silence)
        self.avi = [i for i in range(len(self.pwms))]


class SBConfig:
    def __init__(self, tracks) -> None:
        self.map = {track: None for track in tracks}
        self.snds = set()

    def set_snd(self, tracks, snd):
        for track in tracks:
            self.map[track] = snd
        self.snds.add(snd)

    def snd_need_int(self):
        return min([snd.need_int() for snd in self.snds])

    def snd_interval(self, time):
        for snd in self.snds:
            snd.interval(time)

    def silence(self):
        for snd in self.snds:
            snd.silence()


class SB:
    def __init__(self, filename, sbconfig: SBConfig) -> None:
        self.tempo = 500000
        self.notes = []

        self.time = 0
        for line in open(filename).readlines():
            args = line.split(" ")
            if args[0] == "tempo":
                self.tempo = int(args[1])
                print("tempo: {}".format(self.tempo))
            elif args[0] == "note":
                start = int(args[3])
                noteid = int(args[2])
                track = int(args[5])
                duration = int(args[4])

                playsnd = sbconfig.map[track]
                kf = sbconfig.snd_need_int()
                while kf <= start:
                    self.goto(kf)
                    sbconfig.snd_interval(self.time)
                    kf = sbconfig.snd_need_int()

                self.goto(start)
                print(self.time, noteid)
                playsnd.add(int(args[1]), noteid, start, min(duration, 960), track)

        kf = sbconfig.snd_need_int()
        while kf <= start:
            self.goto(kf)
            sbconfig.snd_interval(self.time)
            kf = sbconfig.snd_need_int()

        sbconfig.silence()

    def goto(self, time):
        tosleep = (time - self.time) * self.tempo / 1000000 / 480
        sleep(tosleep)
        self.time = time
