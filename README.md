# SoundBuzzer

用micropython写的使用蜂鸣器播放音乐的小玩具。

先将midi文件转成**这个项目自定义的sb文件**

在板子上运行程序播放sb文件

## extract.py

```
usage: extract.py [-h] -i INPUT -o OUTPUT

Convert midi to sb

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input midi file
  -o OUTPUT, --output OUTPUT
                        output sb file
```

在主机上运行，将midi文件转成sb文件

## play.py

### SoundManager

每个SoundManager可控制多个蜂鸣器
如果蜂鸣器不够用，SoundManager会优先保证每个音轨有一个音正在被演奏

### SBConf

设置播放属性
现在支持设置音轨，并为每个音轨分配SoundManager，可以把多个音轨分配给同一个SoundManager

### SB

读取sb文件并根据传入的config进行播放

### Example

example.py是示例代码

## TODO

- [ ] 将sb文件优化为二进制存储，减少空间占用
- [ ] 支持变速谱面
- [x] 音量渐变
- [x] 支持音量控制