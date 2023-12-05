import soundbuzzer

b1 = soundbuzzer.Buzzer(soundbuzzer.Buzzer.SOFT, 7, 20)
b2 = soundbuzzer.Buzzer(soundbuzzer.Buzzer.SOFT, 9, 19)
b3 = soundbuzzer.Buzzer(soundbuzzer.Buzzer.SOFT, 11, 18)
b4 = soundbuzzer.Buzzer(soundbuzzer.Buzzer.SOFT, 13, 17)
b5 = soundbuzzer.Buzzer(soundbuzzer.Buzzer.SOFT, 15, 16)

snd0 = soundbuzzer.SoundManager([b1, b2])
snd1 = soundbuzzer.SoundManager([b3, b4, b5])
conf = soundbuzzer.SBConfig([0, 1, 2])
conf.set_snd([0], snd0)
conf.set_snd([1, 2], snd1)

sb = soundbuzzer.SB("weather", conf)
