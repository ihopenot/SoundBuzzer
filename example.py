import soundbuzzer

snd0 = soundbuzzer.SoundManager([6])
snd1 = soundbuzzer.SoundManager([7])
conf = soundbuzzer.SBConfig([0, 1])
conf.set_snd([0], snd0)
conf.set_snd([1], snd1)

soundbuzzer.SB("example.sb", conf)
