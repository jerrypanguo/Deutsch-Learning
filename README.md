# 德语学习助手 (Deutsch Lernhelfer)

这是一个专为德语初学者(高阶也可)设计的命令行学习助手工具,帮助你更轻松地学习德语.

## 功能特点

1. **翻译功能** - 将德语句子翻译成中文,或将中文翻译成德语
2. **语法分析** - 分析德语句子的词性、单词成分和时态
3. **拼写纠错** - 自动检测并纠正德语句子中的拼写和语法错误
4. **发音指导** - 提供德语单词和句子的发音指导和音标展示

## 安装步骤

1. 确保你已安装Python 3.8或更高版本
2. 克隆或下载本项目
3. 创建并激活虚拟环境:

```bash
# 创建虚拟环境
python -m venv venv

# 在Windows上激活虚拟环境
venv\Scripts\activate

# 在macOS/Linux上激活虚拟环境
source venv/bin/activate
```

4. 安装依赖包:

```bash
pip install -r requirements.txt
```

### Mac系统特殊安装步骤

Mac用户可以使用专门的安装脚本进行安装:

```bash
# 赋予脚本执行权限
chmod +x setup_mac.sh

# 运行安装脚本
./setup_mac.sh
```

该脚本会自动创建虚拟环境并安装所有必要的依赖.

### 关于语法检查功能

完整的语法检查功能需要Java环境支持.如果您的系统没有安装Java,程序会自动降级为基本的拼写检查功能.要启用完整的语法检查功能,请确保:

1. 安装Java 8或更高版本
2. 确保`JAVA_HOME`环境变量正确设置

## 使用方法

直接运行主程序:

```bash
# 直接运行Python脚本
python deutsch_cli.py

# 或使用启动脚本(需要先赋予执行权限)
chmod +x start.sh  # 仅Unix/Mac系统需要
./start.sh         # Unix/Mac
start.bat          # Windows
```

进入交互式界面后,你可以选择以下功能:

1. **翻译模式**:输入需要翻译的德语或中文文本
2. **语法分析**:输入德语句子进行词性和语法分析
3. **拼写纠错**:输入德语句子进行拼写和语法检查
4. **发音指导**:输入德语单词获取发音指导

## 示例

```
$ python deutsch_cli.py
欢迎使用德语学习助手!请选择功能:
1. 翻译
2. 语法分析
3. 拼写纠错
4. 发音指导
5. 退出

> 1
请输入要翻译的文本:
Ich lerne Deutsch.
翻译结果:我正在学习德语.

> 2
请输入要分析的德语句子:
Ich lerne Deutsch.
分析结果:
- Ich: 代词,主格
- lerne: 动词,第一人称单数,现在时态
- Deutsch: 名词,中性,宾格

> 3
请输入要纠错的德语句子:
Ich lernen Deutsch.
纠错结果:
- Ich lerne Deutsch. (lernen → lerne)

> 4
请输入要查询发音的德语单词:
Schön
发音指导:[ʃøːn],发"绍恩"的音,嘴唇呈圆形,舌头位置较高
```

## 注意事项

- 本工具需要联网使用,因为翻译和某些语法分析功能依赖外部API
- 对于复杂的语法结构可能存在分析不准确的情况
- 音频播放功能在不同操作系统上的表现可能有所不同
- 在Mac系统上,如果遇到音频播放问题,请确保已安装必要的音频库

## 故障排除

- **语法检查功能不可用**:检查Java环境是否正确安装
- **音频播放失败**:
  - Mac用户:确保已安装`simpleaudio`库或系统支持`afplay`命令
  - Windows用户:确保系统支持默认的音频播放功能
  - Linux用户:确保安装了`aplay`、`paplay`或其他音频播放工具

## 开发信息

- 使用Python 3.8+开发
- 主要依赖包:deep-translator、spacy、language-tool-python、gTTS、pydub等 
