import play

snd0 = play.SoundManager([6])
snd1 = play.SoundManager([7])
conf = play.SBConfig([0, 1])
conf.set_snd([0], snd0)
conf.set_snd([1], snd1)

play.SB("example.sb", conf)
