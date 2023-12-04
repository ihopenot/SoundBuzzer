import mido
from typing import List
import argparse
from utils import Note


class Md:
    def __init__(self, filename) -> None:
        self.tempo = None  # 500000
        self.notes: List[Note] = []
        midi = mido.MidiFile(filename)
        for i, track in enumerate(midi.tracks):
            print("Track {}: {}".format(i, track.name))

            msg: mido.Message
            inst: int = 0
            state = {i: (False, 0) for i in range(119)}  # key state
            now: int = 0

            for msg in track:
                now += msg.time
                if msg.type == "set_tempo":
                    if self.tempo != None:
                        continue
                    self.tempo = msg.tempo
                    print("Tempo: {}".format(msg.tempo))
                elif msg.type == "program_change":
                    inst = msg.program
                    print("Instrument: {}".format(msg.program))
                if msg.type == "note_on":
                    if msg.velocity == 0:
                        if not state[msg.note][0]:
                            continue

                        self.notes.append(
                            Note(
                                inst,
                                msg.note,
                                state[msg.note][1],
                                now - state[msg.note][1],
                                i,
                            )
                        )
                        state[msg.note] = (False, now)
                    else:
                        state[msg.note] = (True, now)
                    # print(msg)
                else:
                    print(msg)
        self.notes = sorted(self.notes, key=lambda x: x.start * 1000 - x.noteid)
        print("done")

    def export(self, filename):
        with open(filename, "w") as f:
            f.write("tempo {}\n".format(self.tempo if self.tempo else 500000))
            for note in self.notes:
                f.write(note.save())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert midi to sb")
    parser.add_argument(
        "-i", "--input", type=str, help="input midi file", required=True
    )
    parser.add_argument(
        "-o", "--output", type=str, help="output sb file", required=True
    )
    args = parser.parse_args()
    md = Md(args.input)
    md.export(args.output)
