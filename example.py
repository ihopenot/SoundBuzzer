import soundbuzzer

snd0 = soundbuzzer.SoundManager([3, 5])
snd1 = soundbuzzer.SoundManager([7, 9])
conf = soundbuzzer.SBConfig([0, 1, 2])
conf.set_snd([0], snd0)
conf.set_snd([1, 2], snd1)

sb = soundbuzzer.SB("weather", conf)
